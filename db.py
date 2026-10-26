# db.py - database connection and schema setup for postgresql

import os
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", 5432)),
    "dbname": os.environ.get("PGDATABASE", "Modelo_CSPC103"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD"),
}


def get_connection():
    # connect to postgresql database
    return psycopg2.connect(**DB_CONFIG)


SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def create_database_if_missing():
    # connect to the default "postgres" database, then create ours when it is not there yet
    server = dict(DB_CONFIG, dbname="postgres")
    conn = psycopg2.connect(**server)
    conn.autocommit = True  # CREATE DATABASE cannot run inside a transaction
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["dbname"],))
            if cur.fetchone() is None:
                # a database name cannot be a %s value, so sql.Identifier quotes it safely
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_CONFIG["dbname"])))
    finally:
        conn.close()


def init_db():
    # create the database and any missing tables from schema.sql; existing rows are kept
    create_database_if_missing()
    with open(SCHEMA_FILE, encoding="utf-8") as schema:
        ddl = schema.read()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reset_database():
    # one transaction clears related tables without dropping the schema
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                TRUNCATE TABLE grade_component_scores, grades, grade_percentages,
                    enrollments, grade_components, grading_periods, class_offerings,
                    students, teachers, subjects, audit_log
                RESTART IDENTITY
            """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("PostgreSQL database initialized successfully.")
