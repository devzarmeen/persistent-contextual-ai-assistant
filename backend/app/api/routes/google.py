import os
import secrets
from threading import Lock
from urllib.parse import urlencode

# ONLY for local HTTP development.
# Remove this in production when using HTTPS.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.models.user import User
from app.services.auth import get_current_user
from app.services.gmail import (
    GMAIL_SCOPES,
    get_google_connection,
    save_google_connection,
    
)


router = APIRouter(
    prefix="/api/integrations/google",
    tags=["Google Integration"],
)


# -------------------------------------------------------------------
# OAuth temporary state storage
# -------------------------------------------------------------------
#
# We must preserve the PKCE code_verifier generated during /connect
# until Google redirects back to /callback.
#
# Key:
#     random OAuth state
#
# Value:
#     {
#         "user_id": user id,
#         "code_verifier": PKCE verifier
#     }
#
# This is intentionally temporary and one-time-use.
#
# IMPORTANT:
# For production with multiple workers/containers, replace this
# in-memory storage with Redis or a database-backed OAuth state table.
# -------------------------------------------------------------------

_oauth_states: dict[str, dict[str, str | int]] = {}
_oauth_states_lock = Lock()


def get_google_flow() -> Flow:
    """
    Create a Google OAuth Flow using the application's Google client
    credentials.

    PKCE remains enabled because google-auth-oauthlib generates a
    code_verifier automatically.
    """

    if not settings.google_client_id:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID is not configured."
        )

    if not settings.google_client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_SECRET is not configured."
        )

    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": (
                "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": (
                "https://oauth2.googleapis.com/token"
            ),
            "redirect_uris": [
                settings.google_redirect_uri,
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=GMAIL_SCOPES,
    )

    flow.redirect_uri = settings.google_redirect_uri

    return flow


@router.get("/connect")
def connect_google(
    current_user: User = Depends(get_current_user),
):
    """
    Start Google OAuth authorization.

    The generated PKCE verifier is stored temporarily against a
    cryptographically random state value.

    The user's database ID is NOT placed directly in the OAuth state.
    """

    try:
        flow = get_google_flow()

        # Cryptographically random OAuth state.
        state = secrets.token_urlsafe(32)

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )

        # flow.authorization_url() generates the PKCE verifier.
        code_verifier = flow.code_verifier

        if not code_verifier:
            raise RuntimeError(
                "Google OAuth PKCE code verifier was not generated."
            )

        # Store state + user + PKCE verifier temporarily.
        with _oauth_states_lock:
            _oauth_states[state] = {
                "user_id": current_user.id,
                "code_verifier": code_verifier,
            }

        return {
            "authorization_url": authorization_url,
            "state": state,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.get("/callback")
def google_callback(
    code: str,
    state: str,
    session: Session = Depends(get_session),
):
    """
    Google OAuth callback.

    Validates the OAuth state, restores the original PKCE verifier,
    exchanges the authorization code for tokens, verifies the Google
    account through Gmail API, and saves the connection.
    """

    if not state:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth state.",
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth authorization code.",
        )

    # ---------------------------------------------------------------
    # Retrieve and consume OAuth state.
    # ---------------------------------------------------------------
    #
    # We consume it immediately so the same callback cannot be
    # successfully replayed.
    #
    with _oauth_states_lock:
        oauth_data = _oauth_states.pop(state, None)

    if not oauth_data:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or expired OAuth state. "
                "Please start Google connection again."
            ),
        )

    try:
        user_id = int(oauth_data["user_id"])
        code_verifier = str(oauth_data["code_verifier"])

    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state data.",
        ) from exc

    # ---------------------------------------------------------------
    # Find local user.
    # ---------------------------------------------------------------

    user = session.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    try:
        # -----------------------------------------------------------
        # Create a NEW Flow for the callback.
        # -----------------------------------------------------------
        #
        # The important part is restoring the code_verifier generated
        # during /connect.
        # -----------------------------------------------------------

        flow = get_google_flow()

        flow.code_verifier = code_verifier

        # Reconstruct the authorization response expected by
        # google-auth-oauthlib.
        authorization_response = (
            f"{settings.google_redirect_uri}"
            f"?{urlencode({'code': code, 'state': state})}"
        )

        # -----------------------------------------------------------
        # Exchange authorization code for Google tokens.
        # -----------------------------------------------------------

        flow.fetch_token(
            authorization_response=authorization_response,
        )

        credentials = flow.credentials

        if not credentials:
            raise RuntimeError(
                "Google OAuth did not return credentials."
            )

        # -----------------------------------------------------------
        # Verify Google account using Gmail API.
        # -----------------------------------------------------------

        gmail_service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        profile = (
            gmail_service.users()
            .getProfile(
                userId="me",
            )
            .execute()
        )

        google_email = profile.get(
            "emailAddress"
        )

        if not google_email:
            raise RuntimeError(
                "Google did not return an email address."
            )

        # -----------------------------------------------------------
        # Save Google connection in existing database.
        # -----------------------------------------------------------

        save_google_connection(
            session=session,
            user_id=user.id,
            credentials=credentials,
            google_email=google_email,
        )

        # -----------------------------------------------------------
        # Success response.
        # -----------------------------------------------------------

        return {
            "success": True,
            "message": "Google account connected successfully.",
            "google_email": google_email,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Google OAuth callback failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc