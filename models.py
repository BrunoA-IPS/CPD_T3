"""
 Implements a simple database of users.

"""

import sqlite3


class Database:
    """Database connectivity."""

    def __init__(self, filename, schema):
        self.filename = filename
        self.schema = schema
        self.conn = sqlite3.connect(filename, check_same_thread=False)

        def dict_factory(cursor, row):
            """Converts table row to dictionary."""
            res = {}
            for idx, col in enumerate(cursor.description):
                res[col[0]] = row[idx]
            return res

        self.conn.row_factory = dict_factory

    def recreate(self):
        """Recreates the database from the schema file."""
        with open(self.schema) as fin:
            self.conn.cursor().executescript(fin.read())

    def execute_query(self, stmt, args=()):
        """Executes a query."""
        res = self.conn.cursor().execute(stmt, args)
        return res

    def execute_update(self, stmt, args=()):
        """Executes an insert or update and returns the last row id."""
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()
        uid = cursor.lastrowid
        cursor.close()
        return uid
