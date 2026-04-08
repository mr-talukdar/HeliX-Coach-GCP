"""Google Calendar OAuth module for HeliX Coach.

This handles Calendar API authorization — PERMISSION to access the user's calendar.
Separate from Firebase Auth (which handles identity).

Flow:
1. User clicks "Connect Calendar" in the frontend
2. Frontend redirects to /api/auth/calendar
3. Backend redirects to Google OAuth consent screen (Calendar scope)
4. User grants permission
5. Google redirects to /api/auth/callback with an authorization code
6. Backend exchanges code for tokens, stores refresh token in AlloyDB
7. Future calendar API calls use the stored refresh token
"""
import os
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import sqlalchemy

logger = logging.getLogger(__name__)

# OAuth Client Configuration
# In production, these should come from Secret Manager
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8080/api/auth/callback")

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_oauth_flow(state: str = None) -> Flow:
    """Create a Google OAuth flow for Calendar authorization.

    Args:
        state: Optional state parameter (usually the user_id) for CSRF protection.
    """
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [OAUTH_REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=CALENDAR_SCOPES,
        redirect_uri=OAUTH_REDIRECT_URI,
    )
    if state:
        flow.state = state

    return flow


def get_authorization_url(user_id: str) -> str:
    """Generate the Google OAuth consent URL for a user.

    Args:
        user_id: The Firebase UID, used as state for CSRF protection.

    Returns:
        The authorization URL to redirect the user to.
    """
    flow = get_oauth_flow(state=user_id)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent to get refresh token
    )
    return auth_url


def exchange_code_for_tokens(authorization_code: str, user_id: str) -> dict:
    """Exchange an authorization code for access and refresh tokens.

    Args:
        authorization_code: The code from Google's OAuth callback.
        user_id: The Firebase UID (from state parameter).

    Returns:
        dict with token info.
    """
    flow = get_oauth_flow()
    flow.fetch_token(code=authorization_code)
    credentials = flow.credentials

    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        "scopes": " ".join(credentials.scopes) if credentials.scopes else "",
    }


def store_user_tokens(user_id: str, tokens: dict, db_pool) -> None:
    """Store the user's OAuth refresh token in AlloyDB.

    Args:
        user_id: The Firebase UID.
        tokens: Dict with refresh_token, token_expiry, scopes.
        db_pool: SQLAlchemy engine/pool.
    """
    with db_pool.connect() as db_conn:
        db_conn.execute(
            sqlalchemy.text("""
                INSERT INTO user_tokens (user_id, encrypted_refresh_token, token_expiry, scopes, updated_at)
                VALUES (:user_id, :refresh_token, :token_expiry, :scopes, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    encrypted_refresh_token = EXCLUDED.encrypted_refresh_token,
                    token_expiry = EXCLUDED.token_expiry,
                    scopes = EXCLUDED.scopes,
                    updated_at = NOW()
            """),
            {
                "user_id": user_id,
                "refresh_token": tokens["refresh_token"],
                "token_expiry": tokens.get("token_expiry"),
                "scopes": tokens.get("scopes", ""),
            }
        )
        db_conn.commit()
    logger.info(f"Stored OAuth tokens for user {user_id}")


def get_user_calendar_service(user_id: str, db_pool):
    """Build a Google Calendar API client using the user's stored OAuth tokens.

    Args:
        user_id: The Firebase UID.
        db_pool: SQLAlchemy engine/pool.

    Returns:
        A Google Calendar API service object, or None if no tokens found.
    """
    with db_pool.connect() as db_conn:
        result = db_conn.execute(
            sqlalchemy.text("""
                SELECT encrypted_refresh_token, scopes FROM user_tokens
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        ).fetchone()

    if not result:
        logger.warning(f"No stored tokens for user {user_id}. Calendar not connected.")
        return None

    refresh_token, scopes = result

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=scopes.split() if scopes else CALENDAR_SCOPES,
    )

    return build("calendar", "v3", credentials=credentials)


def check_calendar_connected(user_id: str, db_pool) -> bool:
    """Check if a user has connected their Google Calendar.

    Args:
        user_id: The Firebase UID.
        db_pool: SQLAlchemy engine/pool.

    Returns:
        True if the user has stored OAuth tokens.
    """
    with db_pool.connect() as db_conn:
        result = db_conn.execute(
            sqlalchemy.text("SELECT 1 FROM user_tokens WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
    return result is not None
