"""
Database connection management for the Opportunity Finder application.

This module is responsible for:
    - Creating and managing SQLite database connections.
    - Initializing the database schema.
    - Ensuring database operations use the configured database file.

The database stores structured job opportunity records extracted
from source posts.
"""



# importing the relevant libraries
import sqlite3
import logging
from pathlib import Path


class DatabaseConnection:
    """
    Manages connections to the SQLite database.
    """

    def __init__(self, database_path: str = 'data/opportunities.db') -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info("Database connection manager initialized.")

    def connect(self) -> sqlite3.Connection:
        """
        Establish and return a connection to the SQLite database.

        Returns:
            An active SQLite database connection.
        """

        try:
            connection = sqlite3.connect(self.database_path)

            # Return rows as dictionary-like objects.
            connection.row_factory = sqlite3.Row

            # Enable foreign key constraint enforcement.
            connection.execute("PRAGMA foreign_keys = ON")

            self.logger.info(
                "Successfully connected to database: %s",
                self.database_path,
            )

            return connection

        except sqlite3.Error:
            self.logger.exception("Failed to connect to SQLite database.")
            raise

    def create_tables(self) -> None:
        """
        Create the database tables if they do not already exist.

        The opportunities table stores structured job opportunity records.
        Each opportunity is uniquely identified by its source post and
        position within that post.

        The candidate_profiles table stores candidate profiles, including
        their professional information and job preferences.

        Raises:
            sqlite3.Error: If table creation fails.
        """

        query = """
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                source_post_id TEXT NOT NULL,
                opportunity_index INTEGER NOT NULL,
                company TEXT,
                role_title TEXT NOT NULL,
                description TEXT,
                seniority TEXT,
                employment_type TEXT,
                required_skills TEXT NOT NULL,
                locations TEXT NOT NULL,
                remote_policy TEXT NOT NULL,
                salary_min REAL,
                salary_max REAL,
                salary_currency TEXT,
                visa_sponsorship TEXT NOT NULL,
                application_url TEXT,
                deadline TEXT,
                status TEXT NOT NULL,
                published_at TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                extraction_confidence REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                indexed_at TEXT,

                UNIQUE (source_post_id, opportunity_index)
            );
        """

        connection = self.connect()

        try:
            connection.execute(query)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS candidate_profiles (
                    candidate_id TEXT PRIMARY KEY,
                    email TEXT,
                    profile_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            self._migrate_opportunities_table(connection)

            connection.commit()
            self.logger.info("Database tables initialized successfully.")

        except sqlite3.Error:
            connection.rollback()
            self.logger.exception("Failed to initialize database tables.")
            raise

        finally:
            connection.close()



    def _migrate_opportunities_table(self, connection: sqlite3.Connection,) -> None:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(opportunities)"
            ).fetchall()
        }

        if "indexed_at" not in columns:
            connection.execute(
                "ALTER TABLE opportunities ADD COLUMN indexed_at TEXT"
            )
            self.logger.info(
                "Added indexed_at column to opportunities table."
            )
