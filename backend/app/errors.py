"""Uniform JSON error shape for the whole API:

    {"error": {"message": "...", "status": 400, "details": {...}}}
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Raise anywhere in a request to return a controlled JSON error."""

    def __init__(self, message, status=400, details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details or {}

    def to_dict(self):
        body = {"message": self.message, "status": self.status}
        if self.details:
            body["details"] = self.details
        return {"error": body}


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _api_error(exc):
        return jsonify(exc.to_dict()), exc.status

    @app.errorhandler(HTTPException)
    def _http_error(exc):
        # Catches 404 / 405 / 415 so clients never receive Werkzeug's HTML page.
        return jsonify({"error": {"message": exc.description, "status": exc.code}}), exc.code

    @app.errorhandler(Exception)
    def _unexpected(exc):
        app.logger.exception("Unhandled exception")
        return jsonify({"error": {"message": "Internal server error", "status": 500}}), 500