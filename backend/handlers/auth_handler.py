"""
auth_handler.py
---------------
Handles user registration and login via Amazon Cognito.

OOP Concepts Demonstrated:
  - INHERITANCE: AuthHandler inherits handle(), parse_body(), build_response(),
    success(), and error() from BaseHandler.
  - POLYMORPHISM: Overrides validate_input() with auth-specific rules.
  - ENCAPSULATION: Cognito client creation and secret hashing are private methods.
"""

import hashlib
import hmac
import logging
import os
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    """
    Handles authentication operations: REGISTER and LOGIN.

    Inherits from BaseHandler (Inheritance).
    The Cognito client and helper methods are encapsulated (private) within
    this class — callers only interact through handle().

    Environment Variables:
        COGNITO_USER_POOL_ID: The Cognito User Pool ID.
        COGNITO_APP_CLIENT_ID: The Cognito App Client ID.
        COGNITO_APP_CLIENT_SECRET: The Cognito App Client Secret (optional).
    """

    # ------------------------------------------------------------------ #
    #  Encapsulation: class-level private config                          #
    # ------------------------------------------------------------------ #
    __ALLOWED_ACTIONS = {"register", "login", "confirm"}

    def __init__(self):
        super().__init__()
        # Encapsulation: Cognito client is private to this class
        self.__cognito = boto3.client("cognito-idp", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        self.__user_pool_id = os.environ["COGNITO_USER_POOL_ID"]
        self.__client_id = os.environ["COGNITO_APP_CLIENT_ID"]
        self.__client_secret = os.environ.get("COGNITO_APP_CLIENT_SECRET", "")

    # ------------------------------------------------------------------ #
    #  ABSTRACT METHOD IMPLEMENTATIONS (required by BaseHandler)          #
    # ------------------------------------------------------------------ #

    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Route to the appropriate auth operation based on the 'action' field.

        Polymorphism: handle() behaves differently for 'register' vs 'login'
        while the same method signature is preserved.
        """
        body = self.parse_body(event)
        action = body.get("action", "").lower()

        if action not in self.__ALLOWED_ACTIONS:
            return self.error(f"Unknown action '{action}'. Must be one of: {self.__ALLOWED_ACTIONS}", 400)

        validation_error = self.validate_input(body)
        if validation_error:
            return self.error(validation_error, 400)

        try:
            if action == "register":
                return self.__register(body)
            elif action == "login":
                return self.__login(body)
            elif action == "confirm":
                return self.__confirm(body)
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            message = exc.response["Error"]["Message"]
            self._logger.error("Cognito ClientError [%s]: %s", error_code, message)
            return self.error(message, 400)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.exception("Unexpected error in AuthHandler.handle()")
            return self.error("Internal server error", 500)

    def validate_input(self, body: Dict[str, Any]) -> Optional[str]:
        """
        Validate auth request fields.

        Overrides BaseHandler.validate_input() with auth-specific rules.
        Polymorphism: different validation logic for each action type.
        """
        action = body.get("action", "")
        email = body.get("email", "").strip()
        password = body.get("password", "")

        if not email:
            return "Email is required."
        if "@" not in email or "." not in email.split("@")[-1]:
            return "Invalid email format."
        if action in {"register", "login"} and len(password) < 8:
            return "Password must be at least 8 characters."
        if action == "register" and not body.get("full_name", "").strip():
            return "Full name is required for registration."
        return None

    # ------------------------------------------------------------------ #
    #  PRIVATE METHODS — encapsulated internal logic                      #
    # ------------------------------------------------------------------ #

    def __compute_secret_hash(self, username: str) -> str:
        """
        Compute the Cognito SECRET_HASH for apps with a client secret.
        Encapsulation: This cryptographic logic is hidden from external callers.
        """
        if not self.__client_secret:
            return ""
        message = username + self.__client_id
        dig = hmac.new(
            self.__client_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        import base64
        return base64.b64encode(dig).decode()

    def __register(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user in the Cognito User Pool."""
        email = body["email"].strip().lower()
        password = body["password"]
        full_name = body.get("full_name", "").strip()

        kwargs = {
            "ClientId": self.__client_id,
            "Username": email,
            "Password": password,
            "UserAttributes": [
                {"Name": "email", "Value": email},
                {"Name": "name", "Value": full_name},
            ],
        }
        secret_hash = self.__compute_secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        response = self.__cognito.sign_up(**kwargs)
        return self.success(
            {
                "message": "Registration successful. Check your email for a confirmation code.",
                "user_confirmed": response.get("UserConfirmed", False),
                "user_sub": response.get("UserSub"),
            },
            201,
        )

    def __login(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate a user and return Cognito JWT tokens."""
        email = body["email"].strip().lower()
        password = body["password"]

        auth_params = {
            "USERNAME": email,
            "PASSWORD": password,
        }
        secret_hash = self.__compute_secret_hash(email)
        if secret_hash:
            auth_params["SECRET_HASH"] = secret_hash

        response = self.__cognito.initiate_auth(
            ClientId=self.__client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_params,
        )
        tokens = response["AuthenticationResult"]
        return self.success(
            {
                "access_token": tokens["AccessToken"],
                "id_token": tokens["IdToken"],
                "refresh_token": tokens["RefreshToken"],
                "expires_in": tokens["ExpiresIn"],
                "message": "Login successful.",
            }
        )

    def __confirm(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Confirm a user's email with the verification code sent by Cognito."""
        email = body.get("email", "").strip().lower()
        code = body.get("confirmation_code", "").strip()
        if not code:
            return self.error("Confirmation code is required.")

        kwargs = {
            "ClientId": self.__client_id,
            "Username": email,
            "ConfirmationCode": code,
        }
        secret_hash = self.__compute_secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        self.__cognito.confirm_sign_up(**kwargs)
        return self.success({"message": "Email confirmed! You may now log in."})


# ------------------------------------------------------------------ #
#  Lambda Entry Point                                                 #
# ------------------------------------------------------------------ #
_handler = AuthHandler()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point for the Auth function."""
    return _handler.handle(event, context)
