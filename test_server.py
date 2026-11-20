import json
import tempfile
import unittest
from pathlib import Path

from server import ItemStore, create_app


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
            self.request("POST", "/putItem/", {"id": "one", "value": "first"})[0],
            201,
        )
        self.assertEqual(
            json.loads(self.request("GET", "/getItems/")[1]),
            [{"id": "one", "value": "first"}],
        )
        self.assertEqual(
            self.request(
                "PATCH", "/patchItem/one/", {"id": "one", "value": "updated"}
            )[0],
            200,
        )
        self.assertEqual(
            json.loads(self.request("GET", "/getItems/")[1])[0]["value"],
            "updated",
        )
        self.assertEqual(self.request("DELETE", "/deleteItem/one/")[0], 200)
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
                b"PATCH /patchItem/{id}/",
                b"DELETE /deleteItem/{id}/",
            ):
                self.assertIn(endpoint, body)

    def test_health_check(self):
        for path in ("/health", "/health/", "/healthz"):
            status, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body), {"status": "ok"})

    def test_update_requires_matching_item_id_and_existing_record(self):
        status, _ = self.request(
            "PATCH", "/patchItem/missing/", {"id": "different", "value": "x"}
        )
        self.assertEqual(status, 400)
        status, _ = self.request(
            "PATCH", "/patchItem/missing/", {"id": "missing", "value": "x"}
        )
        self.assertEqual(status, 404)

    def test_duplicate_create_and_missing_delete_report_conflicts(self):
        self.request("POST", "/putItem/", {"id": "one", "value": "first"})
        status, _ = self.request(
            "POST", "/putItem/", {"id": "one", "value": "second"}
        )
        self.assertEqual(status, 409)
        status, _ = self.request("DELETE", "/deleteItem/missing/")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
