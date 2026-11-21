import json
import os
from pathlib import Path

from flask import Flask, Response, current_app, request

from sqlitedb import DatabaseError, ItemStore

MAX_REQUEST_SIZE = 1024 * 1024


def create_app(store):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_SIZE

    def validate_item_json(item_json, require_id=False):
        if (
            not isinstance(item_json, dict)
            or not isinstance(item_json.get("value"), str)
            or (
                require_id
                and (
                    not isinstance(item_json.get("id"), int)
                    or isinstance(item_json.get("id"), bool)
                )
            )
        ):
            return None, json_response(
                400,
                {
                    "error": (
                        "Item must contain integer field 'id' and string field 'value'"
                        if require_id
                        else "Item must contain string field 'value'"
                    )
                },
            )
        return item_json, None

    def validate_item_id_json(item_json):
        if (
            not isinstance(item_json, dict)
            or not isinstance(item_json.get("id"), int)
            or isinstance(item_json.get("id"), bool)
        ):
            return None, json_response(
                400,
                {"error": "Request body must contain integer field 'id'"},
            )
        return item_json["id"], None

    def json_response(status, payload):
        return Response(
            json.dumps(payload),
            status=status,
            mimetype="application/json",
        )

    @app.errorhandler(DatabaseError)
    def database_error(error):
        current_app.logger.error("Database operation failed: %s", error)
        return json_response(500, {"error": "Internal server error"})

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
        return json_response(200, store.get_items())

    @app.post("/putItem/")
    def put_item():
        item, error = validate_item_json(request.get_json(silent=True))
        if error is not None:
            return error

        store.put_item(item)
        return "", 201

    @app.patch("/patchItem/")
    def patch_item():
        item, error = validate_item_json(
            request.get_json(silent=True), require_id=True
        )
        if error is not None:
            return error

        item_id = item["id"]
        if not store.patch_item(item_id, item):
            return json_response(
                404, {"error": "Item with ID '{}' not found".format(item_id)}
            )
        return "", 200

    @app.delete("/deleteItem/")
    def delete_item():
        item_id, error = validate_item_id_json(request.get_json(silent=True))
        if error is not None:
            return error
        if not store.delete_item(item_id):
            return json_response(
                404, {"error": "Item with ID '{}' not found".format(item_id)}
            )
        return "", 200

    return app


database_path = os.environ.get(
    "ITEMS_DB_PATH", str(Path(__file__).with_name("items.db"))
)
app = create_app(ItemStore(database_path))


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print("Serving items API at http://{}:{}".format(host, port))
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
