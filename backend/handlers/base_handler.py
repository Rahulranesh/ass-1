"""
base_handler.py
---------------
Abstract Base Class for all Lambda handlers.

OOP Concepts Demonstrated:
  - ABSTRACTION: BaseHandler defines the abstract interface (handle, validate_input,
    build_response) that all concrete handlers must implement.
  - ENCAPSULATION: Internal logging and CORS logic are encapsulated here,
    hidden from subclasses.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaseHandler(ABC):
    """
    Abstract base class for all Lambda function handlers.

    All HTTP handlers in this application inherit from BaseHandler and must
    implement the abstract methods: handle() and validate_input().

    Attributes:
        cors_origins (str): Allowed CORS origins for HTTP responses.
        _logger (Logger): Encapsulated logger instance.
    """

    cors_origins: str = "*"  # Restrict to your domain in production

    def __init__(self):
        # Encapsulation: each handler gets its own logger named after its class
        self._logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    #  ABSTRACT METHODS — subclasses MUST override these                  #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Entry point called by the Lambda runtime.

        Args:
            event: AWS Lambda event dict (API Gateway proxy event).
            context: AWS Lambda context object.

        Returns:
            API Gateway proxy response dict.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_input(self, body: Dict[str, Any]) -> Optional[str]:
        """
        Validate the incoming request body.

        Args:
            body: Parsed JSON body from the request.

        Returns:
            An error message string if validation fails, else None.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    #  CONCRETE METHODS — shared behaviour for all handlers               #
    # ------------------------------------------------------------------ #

    def parse_body(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely parse the JSON body from an API Gateway event.

        Encapsulation: Callers do not need to know how the body is extracted
        or decoded — they just call parse_body().
        """
        raw = event.get("body", "{}")
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            self._logger.warning("Failed to parse request body: %s", exc)
            return {}

    def get_cognito_sub(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract the Cognito user sub (UUID) from the JWT authorizer context."""
        try:
            return event["requestContext"]["authorizer"]["claims"]["sub"]
        except (KeyError, TypeError):
            return None

    def build_response(
        self,
        status_code: int,
        body: Any,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build a standard API Gateway proxy response.

        Polymorphism: Subclasses may call this with different body shapes;
        the method serialises any dict/list/str correctly.

        Args:
            status_code: HTTP status code.
            body: Response body (will be JSON-serialised if dict/list).
            extra_headers: Additional HTTP headers to merge in.

        Returns:
            API Gateway proxy response dict.
        """
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": self.cors_origins,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
        }
        if extra_headers:
            headers.update(extra_headers)

        if isinstance(body, (dict, list)):
            serialised = json.dumps(body)
        else:
            serialised = json.dumps({"message": str(body)})

        return {
            "statusCode": status_code,
            "headers": headers,
            "body": serialised,
        }

    def success(self, data: Any, status_code: int = 200) -> Dict[str, Any]:
        """Convenience wrapper for a 2xx success response."""
        return self.build_response(status_code, data)

    def error(self, message: str, status_code: int = 400) -> Dict[str, Any]:
        """Convenience wrapper for an error response."""
        self._logger.error("Returning error %d: %s", status_code, message)
        return self.build_response(status_code, {"error": message})
