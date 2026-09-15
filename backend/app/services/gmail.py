import base64
import html
import re
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import Session, select

from app.config import settings
from app.models.google_connection import GoogleConnection


GMAIL_READONLY_SCOPE = (
    "https://www.googleapis.com/auth/gmail.readonly"
)

GMAIL_SEND_SCOPE = (
    "https://www.googleapis.com/auth/gmail.send"
)

GMAIL_COMPOSE_SCOPE = (
    "https://www.googleapis.com/auth/gmail.compose"
)

CALENDAR_READONLY_SCOPE = (
    "https://www.googleapis.com/auth/calendar.readonly"
)

CALENDAR_EVENTS_SCOPE = (
    "https://www.googleapis.com/auth/calendar.events"
)

GOOGLE_SCOPES = [
    GMAIL_READONLY_SCOPE,
    GMAIL_SEND_SCOPE,
    GMAIL_COMPOSE_SCOPE,
    CALENDAR_READONLY_SCOPE,
    CALENDAR_EVENTS_SCOPE,
]

GMAIL_SCOPES = GOOGLE_SCOPES


def get_google_connection(
    session: Session,
    user_id: int,
) -> GoogleConnection | None:
    return session.exec(
        select(GoogleConnection).where(
            GoogleConnection.user_id == user_id,
            GoogleConnection.is_active.is_(True),
        )
    ).first()


def save_google_connection(
    session: Session,
    user_id: int,
    credentials: Credentials,
    google_email: str,
) -> GoogleConnection:
    existing = get_google_connection(session, user_id)

    expires_at = credentials.expiry

    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    scopes = credentials.scopes or GMAIL_SCOPES
    scopes_string = " ".join(scopes)

    if existing:
        existing.google_email = google_email
        existing.access_token = credentials.token
        existing.refresh_token = (
            credentials.refresh_token
            or existing.refresh_token
        )
        existing.token_uri = (
            credentials.token_uri
            or "https://oauth2.googleapis.com/token"
        )
        existing.client_id = settings.google_client_id
        existing.client_secret = settings.google_client_secret
        existing.scopes = scopes_string
        existing.expires_at = expires_at
        existing.is_active = True
        existing.updated_at = datetime.now(timezone.utc)

        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    connection = GoogleConnection(
        user_id=user_id,
        google_email=google_email,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_uri=(
            credentials.token_uri
            or "https://oauth2.googleapis.com/token"
        ),
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=scopes_string,
        expires_at=expires_at,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    session.add(connection)
    session.commit()
    session.refresh(connection)

    return connection


def build_gmail_credentials(
    connection: GoogleConnection,
) -> Credentials:
    credentials = Credentials(
        token=connection.access_token,
        refresh_token=connection.refresh_token,
        token_uri=connection.token_uri,
        client_id=connection.client_id,
        client_secret=connection.client_secret,
        scopes=(connection.scopes or "").split(),
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    return credentials


def get_gmail_service(
    session: Session,
    user_id: int,
):
    connection = get_google_connection(session, user_id)

    if not connection:
        raise RuntimeError(
            "Google account is not connected. "
            "Connect Google before using Gmail tools."
        )

    credentials = build_gmail_credentials(connection)

    if credentials.token != connection.access_token:
        connection.access_token = credentials.token

        if credentials.expiry:
            connection.expires_at = credentials.expiry

        connection.updated_at = datetime.now(timezone.utc)

        session.add(connection)
        session.commit()

    return build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )


def get_header(
    headers: list[dict[str, str]],
    name: str,
) -> str:
    target = name.lower()

    for header in headers:
        if header.get("name", "").lower() == target:
            return header.get("value", "")

    return ""


def decode_base64url(value: str) -> str:
    if not value:
        return ""

    padding = "=" * (-len(value) % 4)

    return base64.urlsafe_b64decode(
        value + padding
    ).decode(
        "utf-8",
        errors="replace",
    )


def strip_html(value: str) -> str:
    value = re.sub(
        r"<br\s*/?>",
        "\n",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"</p>",
        "\n",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    return html.unescape(value).strip()


def extract_message_body(
    payload: dict[str, Any],
) -> str:
    body = payload.get("body", {})

    if body.get("data"):
        return decode_base64url(body["data"])

    plain_text = ""
    html_text = ""

    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        part_body = part.get("body", {})

        if part_body.get("data"):
            content = decode_base64url(part_body["data"])

            if mime_type == "text/plain":
                plain_text += content
            elif mime_type == "text/html":
                html_text += content

        nested_parts = part.get("parts")

        if nested_parts:
            nested = extract_message_body(
                {"parts": nested_parts}
            )

            if nested:
                plain_text += nested

    if plain_text.strip():
        return plain_text.strip()

    if html_text.strip():
        return strip_html(html_text)

    return ""


def search_emails(
    session: Session,
    user_id: int,
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    query = query.strip()

    if not query:
        return {
            "success": False,
            "error": "Gmail search query cannot be empty.",
        }

    limit = max(1, min(limit, 20))

    try:
        service = get_gmail_service(session, user_id)

        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=limit,
            )
            .execute()
        )

        results = []

        for reference in response.get("messages", []):
            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=reference["id"],
                    format="metadata",
                    metadataHeaders=[
                        "From",
                        "To",
                        "Subject",
                        "Date",
                    ],
                )
                .execute()
            )

            headers = (
                message.get("payload", {})
                .get("headers", [])
            )

            results.append(
                {
                    "id": message.get("id"),
                    "thread_id": message.get("threadId"),
                    "snippet": message.get("snippet", ""),
                    "from": get_header(headers, "From"),
                    "to": get_header(headers, "To"),
                    "subject": get_header(headers, "Subject"),
                    "date": get_header(headers, "Date"),
                }
            )

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results,
        }

    except HttpError as exc:
        return {
            "success": False,
            "error": f"Gmail API error: {exc}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": (
                f"Gmail search failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }


def get_email(
    session: Session,
    user_id: int,
    message_id: str,
) -> dict[str, Any]:
    message_id = message_id.strip()

    if not message_id:
        return {
            "success": False,
            "error": "Gmail message ID cannot be empty.",
        }

    try:
        service = get_gmail_service(session, user_id)

        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        return {
            "success": True,
            "message": {
                "id": message.get("id"),
                "thread_id": message.get("threadId"),
                "from": get_header(headers, "From"),
                "to": get_header(headers, "To"),
                "subject": get_header(headers, "Subject"),
                "date": get_header(headers, "Date"),
                "snippet": message.get("snippet", ""),
                "body": extract_message_body(payload),
            },
        }

    except HttpError as exc:
        return {
            "success": False,
            "error": f"Gmail API error: {exc}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": (
                f"Get email failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }


def create_raw_email(
    to: str,
    subject: str,
    body: str,
) -> str:
    message = MIMEText(
        body,
        "plain",
        "utf-8",
    )

    message["To"] = to
    message["Subject"] = subject

    return base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")


def draft_email(
    session: Session,
    user_id: int,
    to: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    to = to.strip()
    subject = subject.strip()
    body = body.strip()

    if not to or not subject or not body:
        return {
            "success": False,
            "error": "Recipient, subject, and body are required.",
        }

    try:
        service = get_gmail_service(session, user_id)

        raw_message = create_raw_email(
            to=to,
            subject=subject,
            body=body,
        )

        result = (
            service.users()
            .drafts()
            .create(
                userId="me",
                body={
                    "message": {
                        "raw": raw_message,
                    }
                },
            )
            .execute()
        )

        return {
            "success": True,
            "draft": {
                "id": result.get("id"),
                "message_id": (
                    result.get("message", {}).get("id")
                ),
                "thread_id": (
                    result.get("message", {}).get("threadId")
                ),
            },
        }

    except HttpError as exc:
        return {
            "success": False,
            "error": f"Gmail draft error: {exc}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": (
                f"Email draft failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }


def send_email(
    session: Session,
    user_id: int,
    to: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    to = to.strip()
    subject = subject.strip()
    body = body.strip()

    if not to:
        return {
            "success": False,
            "error": "Recipient email is required.",
        }

    if not subject:
        return {
            "success": False,
            "error": "Email subject is required.",
        }

    if not body:
        return {
            "success": False,
            "error": "Email body is required.",
        }

    try:
        service = get_gmail_service(session, user_id)

        result = (
            service.users()
            .messages()
            .send(
                userId="me",
                body={
                    "raw": create_raw_email(
                        to,
                        subject,
                        body,
                    )
                },
            )
            .execute()
        )

        return {
            "success": True,
            "message": {
                "id": result.get("id"),
                "thread_id": result.get("threadId"),
            },
        }

    except HttpError as exc:
        return {
            "success": False,
            "error": f"Gmail send error: {exc}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": (
                f"Email send failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }