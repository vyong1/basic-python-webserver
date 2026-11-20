import json
import os
from pathlib import Path

from flask import Flask, Response, current_app, request

from db import DatabaseError, DuplicateItemError, ItemStore


MAX_REQUEST_SIZE = 1024 * 1024


def create_app(store):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_SIZE

    def validate_item_json(item_json):
        if (
            not isinstance(item_json, dict)
            or not isinstance(item_json.get("id"), str)
            or not isinstance(item_json.get("value"), str)
        ):
            return None, json_response(
                400,
                {"error": "Item must contain string fields 'id' and 'value'"},
            )
        return item_json, None

    def store_error():
        current_app.logger.error("Database operation failed")
        return json_response(500, {"error": "Internal server error"})

    def json_response(status, payload):
        return Response(
            json.dumps(payload),
            status=status,
            mimetype="application/json",
        )

    @app.errorhandler(404)
    def not_found(_error):
        return json_response(404, {"error": "Not found"})

    @app.errorhandler(413)
    def request_too_large(_error):
        return json_response(413, {"error": "Request body is too large"})

    @app.get("/")
    @app.get("/index.html")
    def index():
        body = Path(__file__).with_name("index.html").read_bytes()
        return Response(body, mimetype="text/html")

    @app.get("/health")
    @app.get("/health/")
    @app.get("/healthz")
    def health():
        return json_response(200, {"status": "ok"})

    @app.get("/getItems/")
    def get_items():
        try:
            return json_response(200, store.get_items())
        except DatabaseError:
            return store_error()

    @app.post("/putItem/")
    def put_item():
        item, error = validate_item_json()
        if error is not None:
            return error
        try:
            store.put_item(item)
        except DuplicateItemError:
            return json_response(409, {"error": "An item with this id already exists"})
        except DatabaseError:
            return store_error()
        return "", 201

    @app.patch("/patchItem/<item_id>/")
    def patch_item(item_id):
        item, error = validate_item_json()
        if error is not None:
            return error
        if item["id"] != item_id:
            return json_response(400, {"error": "Item id must match the path id"})
        try:
            updated = store.patch_item(item_id, item)
        except DatabaseError:
            return store_error()
        if not updated:
            return json_response(404, {"error": "Item not found"})
        return "", 200

    @app.delete("/deleteItem/<item_id>/")
    def delete_item(item_id):
        try:
            deleted = store.delete_item(item_id)
        except DatabaseError:
            return store_error()
        if not deleted:
            return json_response(404, {"error": "Item not found"})
        return "", 200

    return app


def main():
    database_path = os.environ.get(
        "ITEMS_DB_PATH", str(Path(__file__).with_name("items.db"))
    )
    store = ItemStore(database_path)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    app = create_app(store)
    print("Serving items API at http://{}:{}".format(host, port))
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
