import json
import tempfile
import unittest
from pathlib import Path

from server import DatabaseError, ItemStore, create_app


class ItemsAPITest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        store = ItemStore(Path(self.temp_dir.name) / "items.db")
        self.client = create_app(store).test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def request(self, method, path, item=None):
        data = None if item is None else json.dumps(item).encode("utf-8")
        response = self.client.open(
            path,
            data=data,
            method=method,
            content_type="application/json" if data is not None else None,
        )
        return response.status_code, response.data

    def test_create_list_update_and_delete(self):
        self.assertEqual(self.request("GET", "/getItems/"), (200, b"[]"))
        self.assertEqual(
            self.request("POST", "/putItem/", {"value": "first"})[0],
            201,
        )
        item = json.loads(self.request("GET", "/getItems/")[1])[0]
        self.assertEqual(
            json.loads(self.request("GET", "/getItems/")[1]),
            [{"id": item["id"], "value": "first"}],
        )
        self.assertEqual(
            self.request(
                "PATCH",
                "/patchItem/",
                {"id": item["id"], "value": "updated"},
            )[0],
            200,
        )
        self.assertEqual(
            json.loads(self.request("GET", "/getItems/")[1])[0]["value"],
            "updated",
        )
        self.assertEqual(
            self.request("DELETE", "/deleteItem/", {"id": item["id"]})[0], 200
        )
        self.assertEqual(self.request("GET", "/getItems/"), (200, b"[]"))

    def test_api_index_is_served_at_root_and_index_path(self):
        for path in ("/", "/index.html"):
            status, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertIn(b"<!doctype html>", body)
            for endpoint in (
                b"GET /health",
                b"GET /getItems/",
                b"POST /putItem/",
                b"PATCH /patchItem/",
                b"DELETE /deleteItem/",
            ):
                self.assertIn(endpoint, body)

    def test_api_index_shows_the_backend_port(self):
        response = self.client.get("/", base_url="http://localhost:8001")
        self.assertIn(b"backend port: <code>8001</code>", response.data)

    def test_health_check(self):
        for path in ("/health", "/health/", "/healthz"):
            status, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body), {"status": "ok"})

    def test_update_and_delete_report_missing_ids(self):
        status, body = self.request(
            "PATCH", "/patchItem/", {"id": 999, "value": "x"}
        )
        self.assertEqual(status, 404)
        self.assertIn("999", json.loads(body)["error"])

        status, body = self.request("DELETE", "/deleteItem/", {"id": 999})
        self.assertEqual(status, 404)
        self.assertIn("999", json.loads(body)["error"])

    def test_create_generates_ids_and_missing_delete_reports_not_found(self):
        self.request("POST", "/putItem/", {"value": "first"})
        self.request("POST", "/putItem/", {"value": "second"})
        items = json.loads(self.request("GET", "/getItems/")[1])
        self.assertEqual([item["id"] for item in items], [1, 2])
        status, body = self.request("DELETE", "/deleteItem/", {"id": 999})
        self.assertEqual(status, 404)
        self.assertIn("999", json.loads(body)["error"])

    def test_database_error_uses_app_error_handler(self):
        class FailingStore:
            def get_items(self):
                raise DatabaseError("database unavailable")

        client = create_app(FailingStore()).test_client()
        response = client.get("/getItems/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.data),
            {"error": "Internal server error"},
        )


if __name__ == "__main__":
    unittest.main()
