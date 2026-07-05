"""
tests/test_handlers.py
-----------------------
Unit tests for BaseHandler, AuthHandler, and StudentHandler.
Uses mocking to isolate from Cognito and PostgreSQL.
"""

import json
import sys
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from handlers.base_handler import BaseHandler
from handlers.auth_handler import AuthHandler
from utils.response_builder import ResponseBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_event(method="POST", body=None, sub=None):
    event = {
        "httpMethod": method,
        "body": json.dumps(body) if body else "{}",
        "headers": {},
        "requestContext": {},
    }
    if sub:
        event["requestContext"] = {
            "authorizer": {"claims": {"sub": sub}}
        }
    return event


# ---------------------------------------------------------------------------
# BaseHandler Abstraction Tests
# ---------------------------------------------------------------------------

class TestBaseHandlerAbstraction:
    """
    Test that BaseHandler cannot be instantiated directly (Abstraction),
    and that its concrete methods work correctly.
    """

    def test_cannot_instantiate_base_handler(self):
        """Abstraction: BaseHandler is abstract — direct instantiation raises TypeError."""
        with pytest.raises(TypeError, match="abstract"):
            BaseHandler()

    def test_concrete_subclass_must_implement_handle(self):
        """Abstraction: subclass missing handle() raises TypeError."""
        class Incomplete(BaseHandler):
            def validate_input(self, body):
                return None
        with pytest.raises(TypeError):
            Incomplete()

    def test_concrete_subclass_must_implement_validate_input(self):
        """Abstraction: subclass missing validate_input() raises TypeError."""
        class Incomplete(BaseHandler):
            def handle(self, event, context):
                return {}
        with pytest.raises(TypeError):
            Incomplete()


# ---------------------------------------------------------------------------
# BaseHandler Method Tests (via a test double)
# ---------------------------------------------------------------------------

class ConcreteHandler(BaseHandler):
    """Minimal concrete implementation for testing BaseHandler methods."""
    def handle(self, event, context):
        return self.success({"ok": True})

    def validate_input(self, body):
        return None


class TestBaseHandlerMethods:

    def setup_method(self):
        self.handler = ConcreteHandler()

    def test_parse_body_valid_json(self):
        event = {"body": '{"key": "value"}'}
        result = self.handler.parse_body(event)
        assert result == {"key": "value"}

    def test_parse_body_none_returns_empty(self):
        result = self.handler.parse_body({"body": None})
        assert result == {}

    def test_parse_body_invalid_json_returns_empty(self):
        result = self.handler.parse_body({"body": "not-json!!!"})
        assert result == {}

    def test_build_response_structure(self):
        resp = self.handler.build_response(200, {"message": "ok"})
        assert resp["statusCode"] == 200
        assert "Content-Type" in resp["headers"]
        assert "Access-Control-Allow-Origin" in resp["headers"]
        body = json.loads(resp["body"])
        assert body == {"message": "ok"}

    def test_success_returns_200(self):
        resp = self.handler.success({"result": 42})
        assert resp["statusCode"] == 200

    def test_error_returns_400_by_default(self):
        resp = self.handler.error("bad input")
        assert resp["statusCode"] == 400
        body = json.loads(resp["body"])
        assert "error" in body

    def test_error_custom_status_code(self):
        resp = self.handler.error("not found", 404)
        assert resp["statusCode"] == 404

    def test_get_cognito_sub_present(self):
        event = make_event(sub="user-sub-123")
        sub = self.handler.get_cognito_sub(event)
        assert sub == "user-sub-123"

    def test_get_cognito_sub_missing_returns_none(self):
        event = {"requestContext": {}}
        sub = self.handler.get_cognito_sub(event)
        assert sub is None


# ---------------------------------------------------------------------------
# AuthHandler Tests
# ---------------------------------------------------------------------------

class TestAuthHandler:

    @patch("handlers.auth_handler.boto3")
    @patch.dict(os.environ, {
        "COGNITO_USER_POOL_ID": "us-east-1_TEST",
        "COGNITO_APP_CLIENT_ID": "test-client-id",
        "AWS_REGION": "us-east-1",
    })
    def test_register_missing_email_returns_400(self, mock_boto3):
        mock_boto3.client.return_value = MagicMock()
        handler = AuthHandler()
        event = make_event(body={"action": "register", "email": "", "password": "Test1234!", "full_name": "Test"})
        resp = handler.handle(event, None)
        assert resp["statusCode"] == 400

    @patch("handlers.auth_handler.boto3")
    @patch.dict(os.environ, {
        "COGNITO_USER_POOL_ID": "us-east-1_TEST",
        "COGNITO_APP_CLIENT_ID": "test-client-id",
        "AWS_REGION": "us-east-1",
    })
    def test_unknown_action_returns_400(self, mock_boto3):
        mock_boto3.client.return_value = MagicMock()
        handler = AuthHandler()
        event = make_event(body={"action": "hack"})
        resp = handler.handle(event, None)
        assert resp["statusCode"] == 400

    @patch("handlers.auth_handler.boto3")
    @patch.dict(os.environ, {
        "COGNITO_USER_POOL_ID": "us-east-1_TEST",
        "COGNITO_APP_CLIENT_ID": "test-client-id",
        "AWS_REGION": "us-east-1",
    })
    def test_password_too_short_returns_400(self, mock_boto3):
        mock_boto3.client.return_value = MagicMock()
        handler = AuthHandler()
        event = make_event(body={
            "action": "register",
            "email": "test@test.com",
            "password": "short",
            "full_name": "Test User",
        })
        resp = handler.handle(event, None)
        assert resp["statusCode"] == 400
        body = json.loads(resp["body"])
        assert "Password" in body.get("error", "")


# ---------------------------------------------------------------------------
# ResponseBuilder Polymorphism Tests
# ---------------------------------------------------------------------------

class TestResponseBuilderPolymorphism:
    """Test polymorphic ResponseBuilder class methods."""

    def test_ok_returns_200(self):
        resp = ResponseBuilder.ok({"data": "test"})
        assert resp["statusCode"] == 200

    def test_created_returns_201(self):
        resp = ResponseBuilder.created({"id": "123"})
        assert resp["statusCode"] == 201

    def test_bad_request_returns_400(self):
        resp = ResponseBuilder.bad_request("Invalid input")
        assert resp["statusCode"] == 400

    def test_unauthorized_returns_401(self):
        resp = ResponseBuilder.unauthorized()
        assert resp["statusCode"] == 401

    def test_not_found_returns_404(self):
        resp = ResponseBuilder.not_found("Student")
        assert resp["statusCode"] == 404
        body = json.loads(resp["body"])
        assert "Student not found" in body["error"]

    def test_internal_error_returns_500(self):
        resp = ResponseBuilder.internal_error()
        assert resp["statusCode"] == 500

    def test_all_responses_have_cors_headers(self):
        """Polymorphism: all response builders include CORS headers."""
        responses = [
            ResponseBuilder.ok({}),
            ResponseBuilder.created({}),
            ResponseBuilder.bad_request("err"),
            ResponseBuilder.unauthorized(),
            ResponseBuilder.not_found(),
            ResponseBuilder.internal_error(),
        ]
        for resp in responses:
            assert "Access-Control-Allow-Origin" in resp["headers"]

    def test_paginated_includes_pagination_meta(self):
        resp = ResponseBuilder.paginated(items=[1, 2, 3], total=30, page=1, per_page=3)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert "pagination" in body
        assert body["pagination"]["total"] == 30
        assert body["pagination"]["pages"] == 10
