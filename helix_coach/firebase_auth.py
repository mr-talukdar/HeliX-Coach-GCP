"""Firebase Authentication module for HeliX Coach.

Uses Firebase Admin SDK to verify ID tokens sent from the Next.js frontend.
This handles user identity — WHO the user is.
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger(__name__)

_initialized = False


def _init_firebase():
    """Initialize Firebase Admin SDK (once)."""
    global _initialized
    if _initialized:
        return

    try:
        firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
        if firebase_key:
            cred = credentials.Certificate(firebase_key)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()

        _initialized = True
        logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and extract user info.

    Args:
        id_token: The Firebase ID token from the frontend.

    Returns:
        dict with keys: uid, email, name, picture
        
    Raises:
        ValueError: If the token is invalid.
        firebase_admin.auth.InvalidIdTokenError: If token verification fails.
    """
    _init_firebase()

    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email", ""),
            "name": decoded_token.get("name", ""),
            "picture": decoded_token.get("picture", ""),
        }
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase ID token: {e}")
        raise ValueError(f"Invalid authentication token: {e}") from e
    except auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired Firebase ID token: {e}")
        raise ValueError("Authentication token has expired. Please sign in again.") from e
    except Exception as e:
        logger.error(f"Unexpected error verifying Firebase token: {e}")
        raise
