import sqlite3
from contextlib import contextmanager


class DatabaseError(Exception):
    pass


class DuplicateItemError(DatabaseError):
    pass


class ItemStore:
    def __init__(self, database_path):
        self.database_path = str(database_path)
        try:
            with self._connection() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS items (
                        id TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def get_items(self):
        try:
            with self._connection() as connection:
                rows = connection.execute(
                    "SELECT id, value FROM items ORDER BY id"
                ).fetchall()
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error
        return [{"id": item_id, "value": value} for item_id, value in rows]

    def put_item(self, item):
        try:
            with self._connection() as connection:
                connection.execute(
                    "INSERT INTO items (id, value) VALUES (?, ?)",
                    (item["id"], item["value"]),
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateItemError(str(error)) from error
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    def patch_item(self, item_id, item):
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE items SET value = ? WHERE id = ?",
                    (item["value"], item_id),
                )
                return cursor.rowcount > 0
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    def delete_item(self, item_id):
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "DELETE FROM items WHERE id = ?", (item_id,)
                )
                return cursor.rowcount > 0
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error
