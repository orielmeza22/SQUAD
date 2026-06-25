"""Database schema introspection helpers (SQLite + PostgreSQL).

Migrated 1:1 from the legacy monolith ``get_sqlite_schema`` / ``get_postgres_schema``.
"""

import sqlite3
from typing import Dict, Any, List


def get_sqlite_schema(db_path: str) -> Dict[str, Any]:
    """Introspect a SQLite database into a {table: {columns, foreign_keys}} dict.

    Args:
        db_path: Path to the ``.db`` / ``.sqlite`` file.

    Returns:
        Mapping of table name to its columns and foreign keys.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']

    schema: Dict[str, Any] = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols_info = cursor.fetchall()
        columns: List[Dict[str, Any]] = []
        for col in cols_info:
            columns.append({
                "name": col[1],
                "type": col[2],
                "pk": bool(col[5])
            })

        cursor.execute(f"PRAGMA foreign_key_list({table});")
        fks_info = cursor.fetchall()
        foreign_keys: List[Dict[str, Any]] = []
        for fk in fks_info:
            foreign_keys.append({
                "from": fk[3],
                "table": fk[2],
                "to": fk[4]
            })

        schema[table] = {"columns": columns, "foreign_keys": foreign_keys}
    conn.close()
    return schema


def get_postgres_schema(db_url: str) -> Dict[str, Any]:
    """Introspect a PostgreSQL database into a {table: {columns, foreign_keys}} dict.

    Args:
        db_url: SQLAlchemy/psycopg2 connection URL.

    Returns:
        Mapping of table name to its columns and foreign keys.
    """
    import psycopg2  # lazy import; only needed when Postgres is used

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    tables = [row[0] for row in cursor.fetchall()]

    schema: Dict[str, Any] = {}
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type,
                   (SELECT EXISTS (
                       SELECT 1 FROM information_schema.table_constraints tc
                       JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                       WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = '{table}' AND kcu.column_name = c.column_name
                   )) as is_pk
            FROM information_schema.columns c
            WHERE table_name = '{table}';
        """)
        cols_info = cursor.fetchall()
        columns: List[Dict[str, Any]] = []
        for col in cols_info:
            columns.append({
                "name": col[0],
                "type": col[1],
                "pk": bool(col[2])
            })

        cursor.execute(f"""
            SELECT
                kcu.column_name AS local_column,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='{table}';
        """)
        fks_info = cursor.fetchall()
        foreign_keys: List[Dict[str, Any]] = []
        for fk in fks_info:
            foreign_keys.append({
                "from": fk[0],
                "table": fk[1],
                "to": fk[2]
            })

        schema[table] = {"columns": columns, "foreign_keys": foreign_keys}
    conn.close()
    return schema
