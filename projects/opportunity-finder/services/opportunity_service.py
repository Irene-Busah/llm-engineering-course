"""
Opportunity management service for the Opportunity Finder application.

This module is responsible for:
    - Converting extracted opportunity drafts into complete Opportunity records.
    - Managing opportunity metadata and system-generated fields.
    - Persisting opportunity records in the SQLite database.
    - Preventing duplicate opportunity records.

It acts as the bridge between the opportunity extraction agent
and the database layer.
"""


# importing the libraries
import json
import logging
import sqlite3
import uuid

from datetime import datetime, timezone

from database.connection import DatabaseConnection
from models.opportunity import Opportunity, OpportunityDraft, OpportunityStatus, OpportunityExtractionResult
from models.post import SourcePost
from services.embedding_service import EmbeddingService
from database.vector_store import VectorStore



class OpportunityService:
    """
    Handles the creation and persistence of job opportunities
    """

    def __init__(self, database: DatabaseConnection, embedding_service: EmbeddingService, vector_store: VectorStore) -> None:
        self.database = database
        self.embedding_service = embedding_service
        self.vector_store = vector_store

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('Opportunity Service Initialized.')


    def _row_to_opportunity(self, row: sqlite3.Row, columns: list[str],) -> Opportunity:
        """
        Convert a SQLite row into a validated Opportunity object.
        """

        data = dict(zip(columns, row))

        data["required_skills"] = json.loads(data["required_skills"])
        data["locations"] = json.loads(data["locations"])

        for field in (
            "deadline",
            "published_at",
            "first_seen_at",
            "last_seen_at",
            "created_at",
            "updated_at",
            "indexed_at",
        ):
            if data[field] is not None:
                data[field] = datetime.fromisoformat(data[field])

        return Opportunity.model_validate(data)

    def create_opportunity(self, draft: OpportunityDraft, post: SourcePost, opportunity_index: int) -> Opportunity:
        """
        Convert an extracted opportunity draft into a complete Opportunity record.

        Args:
            draft: The opportunity data extracted by the LLM.
            post: The original source post containing the opportunity.
            opportunity_index: The opportunity's position within the source post.

        Returns:
            A complete Opportunity object.
        """

        now = datetime.now(timezone.utc)

        opportunity = Opportunity(
            id=str(uuid.uuid4()),
            source_post_id=post.source_post_id,
            opportunity_index=opportunity_index,
            company=draft.company,
            role_title=draft.role_title,
            description=draft.description,
            seniority=draft.seniority,
            employment_type=draft.employment_type,
            required_skills=draft.required_skills,
            locations=draft.locations,
            remote_policy=draft.remote_policy,
            salary_min=draft.salary_min,
            salary_max=draft.salary_max,
            salary_currency=draft.salary_currency,
            visa_sponsorship=draft.visa_sponsorship,
            application_url=draft.application_url,
            deadline=draft.deadline,
            status=OpportunityStatus.UNKNOWN,
            published_at=post.published_at,
            first_seen_at=post.fetched_at,
            last_seen_at=post.fetched_at,
            extraction_confidence=None,
            created_at=now,
            updated_at=now,
        )

        self.logger.info(
            "Created opportunity record: %s - %s",
            opportunity.company,
            opportunity.role_title,
        )

        return opportunity


    def save_opportunities(self, opportunities: list[Opportunity]) -> list[str]:
        """
        Save opportunity records to the SQLite database.

        Duplicate opportunities are ignored using the unique combination
        of source_post_id and opportunity_index.

        Args:
            opportunities: A list of complete Opportunity records.

        Returns:
            The number of newly inserted opportunities.
        """
        if not opportunities:
            self.logger.info("No opportunities to save.")
            return 0

        query = """
            INSERT OR IGNORE INTO opportunities (
                id,
                source_post_id,
                opportunity_index,
                company,
                role_title,
                description,
                seniority,
                employment_type,
                required_skills,
                locations,
                remote_policy,
                salary_min,
                salary_max,
                salary_currency,
                visa_sponsorship,
                application_url,
                deadline,
                status,
                published_at,
                first_seen_at,
                last_seen_at,
                extraction_confidence,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            );
        """

        records = [
            (
                opportunity.id,
                opportunity.source_post_id,
                opportunity.opportunity_index,
                opportunity.company,
                opportunity.role_title,
                opportunity.description,
                opportunity.seniority,
                opportunity.employment_type,
                json.dumps(opportunity.required_skills),
                json.dumps(opportunity.locations),
                opportunity.remote_policy.value,
                opportunity.salary_min,
                opportunity.salary_max,
                opportunity.salary_currency,
                opportunity.visa_sponsorship.value,
                str(opportunity.application_url) if opportunity.application_url else None,
                opportunity.deadline.isoformat() if opportunity.deadline else None,
                opportunity.status.value,
                opportunity.published_at.isoformat() if opportunity.published_at else None,
                opportunity.first_seen_at.isoformat(),
                opportunity.last_seen_at.isoformat(),
                opportunity.extraction_confidence,
                opportunity.created_at.isoformat(),
                opportunity.updated_at.isoformat(),
            )
            for opportunity in opportunities
        ]

        connection = self.database.connect()

        try:
            cursor = connection.executemany(query, records)
            connection.commit()

            saved_ids = [
                opportunity.id
                for opportunity in opportunities
                if opportunity.id in {
                    row[0]
                    for row in connection.execute(
                        "SELECT id FROM opportunities WHERE id IN ({})".format(
                            ",".join("?" for _ in opportunities)
                        ),
                        [opportunity.id for opportunity in opportunities],
                    ).fetchall()
                }
            ]

            self.logger.info(
                "Saved %d new opportunities out of %d submitted.",
                len(saved_ids),
                len(opportunities),
            )

            return saved_ids

        except sqlite3.Error:
            connection.rollback()
            self.logger.exception("Failed to save opportunities.")
            raise

        finally:
            connection.close()


    def process_extraction(self, result: OpportunityExtractionResult, post: SourcePost,) -> int:
        """
        Process an extraction result, persist opportunities, and index
        newly saved opportunities in ChromaDB.

        Args:
            result: The extraction result returned by the LLM.
            post: The original source post.

        Returns:
            The number of newly saved opportunities.
        """
        if not result.is_opportunity or not result.opportunities:
            self.logger.info(
                "No opportunities found in source post %s. Reason: %s",
                post.source_post_id,
                result.rejection_reason,
            )
            return 0

        opportunities = [
            self.create_opportunity(
                draft=draft,
                post=post,
                opportunity_index=index,
            )
            for index, draft in enumerate(result.opportunities)
        ]

        saved_ids = self.save_opportunities(opportunities)

        self.logger.info(
            "Processed source post %s: %d opportunities saved to SQLite.",
            post.source_post_id,
            len(saved_ids),
        )

        return len(saved_ids)

    


    def list_opportunities(
        self,
        limit: int = 20,
        offset: int = 0,
        role: str | None = None,
        company: str | None = None,
        location: str | None = None,
        status=None,
        remote_policy=None,
    ) -> tuple[list[Opportunity], int]:
        """
        Browse opportunities with pagination and optional filters.

        Returns the page of opportunities and the total number matching
        the supplied filters. Results are newest first.
        """
        if limit < 1 or offset < 0:
            raise ValueError("limit must be positive and offset cannot be negative.")

        conditions: list[str] = []
        parameters: list[object] = []

        if role:
            conditions.append("role_title LIKE ?")
            parameters.append(f"%{role.strip()}%")

        if company:
            conditions.append("company LIKE ?")
            parameters.append(f"%{company.strip()}%")

        if location:
            conditions.append("locations LIKE ?")
            parameters.append(f"%{location.strip()}%")

        if status:
            conditions.append("status = ?")
            parameters.append(getattr(status, "value", status))

        if remote_policy:
            conditions.append("remote_policy = ?")
            parameters.append(getattr(remote_policy, "value", remote_policy))

        where_clause = (
            "WHERE " + " AND ".join(conditions)
            if conditions
            else ""
        )

        count_query = f"SELECT COUNT(*) FROM opportunities {where_clause}"
        page_query = f"""
            SELECT *
            FROM opportunities
            {where_clause}
            ORDER BY published_at DESC, created_at DESC
            LIMIT ? OFFSET ?
        """

        connection = self.database.connect()
        try:
            total = connection.execute(
                count_query,
                parameters,
            ).fetchone()[0]

            cursor = connection.execute(
                page_query,
                [*parameters, limit, offset],
            )
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]

            items = [
                self._row_to_opportunity(row, columns)
                for row in rows
            ]

            return items, total

        except sqlite3.Error:
            self.logger.exception("Failed to list opportunities.")
            raise
        finally:
            connection.close()


    def get_opportunity(self, opportunity_id: str) -> Opportunity | None:
        """
        Retrieve an opportunity by its ID.

        Args:
            opportunity_id: Unique opportunity identifier.

        Returns:
            The matching Opportunity object, or None if not found.
        """

        query = "SELECT * FROM opportunities WHERE id = ?"

        connection = self.database.connect()

        try:
            cursor = connection.execute(query, (opportunity_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            columns = [column[0] for column in cursor.description]

            return self._row_to_opportunity(row, columns)

        except sqlite3.Error:
            self.logger.exception(
                "Failed to retrieve opportunity: %s",
                opportunity_id,
            )
            raise

        finally:
            connection.close()
            


    def get_unindexed_opportunities(self) -> list[Opportunity]:
        """
        Retrieve opportunities that have not yet been indexed in ChromaDB.

        Returns:
            A list of opportunities whose indexed_at field is NULL.
        """

        query = """
            SELECT *
            FROM opportunities
            WHERE indexed_at IS NULL
        """

        connection = self.database.connect()

        try:
            cursor = connection.execute(query)
            rows = cursor.fetchall()

            columns = [column[0] for column in cursor.description]

            opportunities = []

            for row in rows:
                data = dict(zip(columns, row))

                data["required_skills"] = json.loads(data["required_skills"])
                data["locations"] = json.loads(data["locations"])

                for field in (
                    "deadline",
                    "published_at",
                    "first_seen_at",
                    "last_seen_at",
                    "created_at",
                    "updated_at",
                    "indexed_at",
                ):
                    if data[field] is not None:
                        data[field] = datetime.fromisoformat(data[field])

                opportunities.append(Opportunity.model_validate(data))

            self.logger.info(
                "Found %d opportunities awaiting vector indexing.",
                len(opportunities),
            )

            return opportunities

        except sqlite3.Error:
            self.logger.exception(
                "Failed to retrieve opportunities awaiting indexing."
            )
            raise

        finally:
            connection.close()


    def mark_as_indexed(self, opportunity_id: str) -> None:
        """
        Mark an opportunity as successfully indexed in ChromaDB.

        Args:
            opportunity_id: The ID of the indexed opportunity.
        """

        query = """
            UPDATE opportunities
            SET indexed_at = ?
            WHERE id = ?
        """

        indexed_at = datetime.now(timezone.utc).isoformat()

        connection = self.database.connect()

        try:
            cursor = connection.execute(query, (indexed_at, opportunity_id))
            connection.commit()

            if cursor.rowcount == 0:
                self.logger.warning(
                    "No opportunity found to update: %s",
                    opportunity_id,
                )
                return

            self.logger.info(
                "Marked opportunity %s as indexed.",
                opportunity_id,
            )

        except sqlite3.Error:
            connection.rollback()
            self.logger.exception(
                "Failed to update indexing status for opportunity %s.",
                opportunity_id,
            )
            raise

        finally:
            connection.close()



    def index_pending_opportunities(self) -> int:
        """
        Index all opportunities that have not yet been indexed.

        Failed indexing attempts remain pending for future retries.

        Returns:
            Number of successfully indexed opportunities.
        """

        opportunities = self.get_unindexed_opportunities()

        if not opportunities:
            self.logger.info("No opportunities awaiting indexing.")
            return 0

        indexed_count = 0

        for opportunity in opportunities:
            try:
                self.embedding_service.index_opportunity(
                    opportunity=opportunity,
                    vector_store=self.vector_store,
                )

                self.mark_as_indexed(opportunity.id)
                indexed_count += 1

            except Exception:
                self.logger.exception(
                    "Failed to index opportunity %s. It will be retried later.",
                    opportunity.id,
                )

        self.logger.info(
            "Indexing completed: %d of %d opportunities successfully indexed.",
            indexed_count,
            len(opportunities),
        )

        return indexed_count


    def get_opportunities_by_ids(self, opportunity_ids: list[str],) -> list[Opportunity]:
        """
        Retrieve multiple opportunities using their IDs.

        Args:
            opportunity_ids: List of opportunity identifiers.

        Returns:
            Matching Opportunity objects.
        """

        if not opportunity_ids:
            return []

        placeholders = ", ".join("?" for _ in opportunity_ids)

        query = f"""
            SELECT *
            FROM opportunities
            WHERE id IN ({placeholders})
        """

        connection = self.database.connect()

        try:
            cursor = connection.execute(query, opportunity_ids)
            rows = cursor.fetchall()

            columns = [column[0] for column in cursor.description]

            opportunities = [
                self._row_to_opportunity(row, columns)
                for row in rows
            ]

            self.logger.info(
                "Retrieved %d of %d requested opportunities.",
                len(opportunities),
                len(opportunity_ids),
            )

            return opportunities

        except sqlite3.Error:
            self.logger.exception(
                "Failed to retrieve opportunities by IDs."
            )
            raise

        finally:
            connection.close()
