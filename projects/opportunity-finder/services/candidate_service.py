
import logging
import sqlite3
from datetime import datetime, timezone

from models.candidate import CandidateProfile


class CandidateService:

    def __init__(self, database):
        self.database = database
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Candidate service initialized.")

    def save_candidate_profile(self, candidate_profile: CandidateProfile,) -> None:
        """Save a new candidate profile or update an existing one."""

        connection = self.database.connect()

        try:
            profile_data = candidate_profile.model_dump_json()
            now = datetime.now(timezone.utc).isoformat()

            connection.execute(
                """
                INSERT INTO candidate_profiles (
                    candidate_id,
                    email,
                    profile_data,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(candidate_id) DO UPDATE SET
                    email = excluded.email,
                    profile_data = excluded.profile_data,
                    updated_at = excluded.updated_at
                """,
                (
                    candidate_profile.candidate_id,
                    str(candidate_profile.email)
                    if candidate_profile.email else None,
                    profile_data,
                    now,
                    now,
                ),
            )

            connection.commit()
            self.logger.info(
                "Candidate profile saved: %s",
                candidate_profile.candidate_id,
            )

        except sqlite3.Error:
            connection.rollback()
            self.logger.exception("Failed to save candidate profile.")
            raise

        finally:
            connection.close()



    def get_candidate_profile(
        self,
        candidate_id: str,
    ) -> CandidateProfile | None:
        """Retrieve a candidate profile using its ID."""

        connection = self.database.connect()

        try:
            cursor = connection.execute(
                """
                SELECT profile_data
                FROM candidate_profiles
                WHERE candidate_id = ?
                """,
                (candidate_id,),
            )

            row = cursor.fetchone()

            if row is None:
                self.logger.info(
                    "Candidate profile not found: %s",
                    candidate_id,
                )
                return None

            candidate_profile = CandidateProfile.model_validate_json(
                row["profile_data"]
            )

            self.logger.info(
                "Candidate profile retrieved: %s",
                candidate_id,
            )

            return candidate_profile

        except (sqlite3.Error, ValueError):
            self.logger.exception("Failed to retrieve candidate profile.")
            raise

        finally:
            connection.close()

    def update_candidate_profile(
        self,
        candidate_profile: CandidateProfile,
    ) -> None:
        """Update an existing candidate profile."""

        connection = self.database.connect()

        try:
            profile_data = candidate_profile.model_dump_json()

            cursor = connection.execute(
                """
                UPDATE candidate_profiles
                SET email = ?,
                    profile_data = ?,
                    updated_at = ?
                WHERE candidate_id = ?
                """,
                (
                    str(candidate_profile.email)
                    if candidate_profile.email else None,
                    profile_data,
                    candidate_profile.updated_at.isoformat(),
                    candidate_profile.candidate_id,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Candidate profile not found: "
                    f"{candidate_profile.candidate_id}"
                )

            connection.commit()

            self.logger.info(
                "Candidate profile updated: %s",
                candidate_profile.candidate_id,
            )

        except (sqlite3.Error, ValueError):
            connection.rollback()
            self.logger.exception("Failed to update candidate profile.")
            raise

        finally:
            connection.close()
