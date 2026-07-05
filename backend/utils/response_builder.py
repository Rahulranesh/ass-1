"""
response_builder.py
-------------------
Polymorphic response builder utility.

OOP Concepts Demonstrated:
  - POLYMORPHISM: Different build_* methods return the same dict shape
    but with different content, status codes, and metadata.
  - ABSTRACTION: Callers use named methods without caring about the
    underlying dict structure.
"""

from typing import Any, Dict, List, Optional


class ResponseBuilder:
    """
    Builds standardized API Gateway proxy response dicts.

    Polymorphism: each class method returns the same dict shape but for
    different scenarios — success, created, error, not_found, unauthorized, etc.

    Abstraction: callers use descriptive class methods without constructing
    the response dict manually.

    All methods are class methods (no instance state required).
    """

    _CORS_HEADERS: Dict[str, str] = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    @classmethod
    def _base(
        cls,
        status_code: int,
        body: Any,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Internal base builder. Not part of the public polymorphic interface."""
        import json

        headers = dict(cls._CORS_HEADERS)
        if extra_headers:
            headers.update(extra_headers)

        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(body),
        }

    # ------------------------------------------------------------------ #
    #  POLYMORPHIC PUBLIC METHODS                                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def ok(cls, data: Any) -> Dict[str, Any]:
        """200 OK — standard success response."""
        return cls._base(200, {"status": "success", "data": data})

    @classmethod
    def created(cls, data: Any, message: str = "Resource created.") -> Dict[str, Any]:
        """201 Created — resource was successfully created."""
        return cls._base(201, {"status": "success", "message": message, "data": data})

    @classmethod
    def bad_request(cls, message: str, details: Optional[List[str]] = None) -> Dict[str, Any]:
        """400 Bad Request — invalid input."""
        body: Dict[str, Any] = {"status": "error", "error": message}
        if details:
            body["details"] = details
        return cls._base(400, body)

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized.") -> Dict[str, Any]:
        """401 Unauthorized — missing or invalid JWT."""
        return cls._base(401, {"status": "error", "error": message})

    @classmethod
    def forbidden(cls, message: str = "Forbidden.") -> Dict[str, Any]:
        """403 Forbidden — authenticated but not authorized."""
        return cls._base(403, {"status": "error", "error": message})

    @classmethod
    def not_found(cls, resource: str = "Resource") -> Dict[str, Any]:
        """404 Not Found — requested resource does not exist."""
        return cls._base(404, {"status": "error", "error": f"{resource} not found."})

    @classmethod
    def conflict(cls, message: str) -> Dict[str, Any]:
        """409 Conflict — e.g., duplicate email during registration."""
        return cls._base(409, {"status": "error", "error": message})

    @classmethod
    def internal_error(cls, message: str = "An internal server error occurred.") -> Dict[str, Any]:
        """500 Internal Server Error."""
        return cls._base(500, {"status": "error", "error": message})

    @classmethod
    def options(cls) -> Dict[str, Any]:
        """200 response for CORS preflight OPTIONS requests."""
        return cls._base(200, {})

    @classmethod
    def paginated(
        cls,
        items: List[Any],
        total: int,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """
        200 with pagination metadata — used for list endpoints.
        Polymorphism: same HTTP 200 but with a different body shape.
        """
        return cls._base(
            200,
            {
                "status": "success",
                "data": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                },
            },
        )
