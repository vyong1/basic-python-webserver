import sqlite3
from contextlib import contextmanager


class DatabaseError(Exception):
    pass


class ItemStore:
    def __init__(self, database_path):
        self.database_path = str(database_path)
        self._execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _execute(self, query, params=None):
        try:
            with self._connection() as connection:
                cursor = connection.execute(query, params or ())
                return cursor.fetchall()
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    def get_items(self):
        rows = self._execute("SELECT * FROM items ORDER BY id")
        return [{"id": item_id, "value": value} for item_id, value in rows]

    def put_item(self, item):
        self._execute("INSERT INTO items (value) VALUES (?)", (item["value"],))

    def patch_item(self, item_id, item):
        self._execute(
            "UPDATE items SET value = ? WHERE id = ?", (item["value"], item_id)
        )

    def delete_item(self, item_id):
        self._execute("DELETE FROM items WHERE id = ?", (item_id,))
