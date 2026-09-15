from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import Session

from app.services.gmail import (
    CALENDAR_EVENTS_SCOPE,
    CALENDAR_READONLY_SCOPE,
    build_gmail_credentials,
    get_google_connection,
)


def _error(message: str) -> dict[str, Any]:
    return {
        "success": False,
        "error": message,
    }


def _parse_datetime(
    value: str,
    timezone_name: str = "UTC",
) -> datetime:
    if not value:
        raise ValueError(
            "Datetime must be a non-empty ISO 8601 string."
        )

    normalized = value.strip()

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Invalid ISO 8601 datetime: {value}"
        ) from exc

    try:
        tz = ZoneInfo(timezone_name)
    except Exception as exc:
        raise ValueError(
            f"Invalid timezone: {timezone_name}"
        ) from exc

    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)

    return dt.astimezone(tz)


def _clean_event(
    event: dict[str, Any],
) -> dict[str, Any]:
    start = event.get("start", {})
    end = event.get("end", {})

    organizer = event.get("organizer") or {}

    attendees = [
        {
            "email": attendee.get("email"),
            "display_name": attendee.get("displayName"),
            "response_status": attendee.get("responseStatus"),
            "organizer": attendee.get("organizer", False),
            "self": attendee.get("self", False),
        }
        for attendee in event.get("attendees") or []
    ]

    return {
        "id": event.get("id"),
        "status": event.get("status"),
        "summary": event.get("summary"),
        "description": event.get("description"),
        "location": event.get("location"),
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "start_timezone": start.get("timeZone"),
        "end_timezone": end.get("timeZone"),
        "html_link": event.get("htmlLink"),
        "organizer": {
            "email": organizer.get("email"),
            "display_name": organizer.get("displayName"),
            "self": organizer.get("self", False),
        },
        "attendees": attendees,
        "calendar_id": event.get("organizer", {}).get("email"),
    }


def _get_calendar_credentials(
    session: Session,
    user_id: int,
    required_scope: str,
):
    connection = get_google_connection(
        session,
        user_id,
    )

    if not connection:
        raise RuntimeError(
            "Google account is not connected. "
            "Connect your Google account first."
        )

    scopes = set(
        (connection.scopes or "").split()
    )

    if required_scope not in scopes:
        raise RuntimeError(
            "Required Google Calendar permission is not granted. "
            "Reconnect Google to grant Calendar access."
        )

    credentials = build_gmail_credentials(connection)

    if credentials.token != connection.access_token:
        connection.access_token = credentials.token

        if credentials.expiry:
            connection.expires_at = credentials.expiry

        session.add(connection)
        session.commit()

    return credentials


def get_calendar_service(
    session: Session,
    user_id: int,
):
    credentials = _get_calendar_credentials(
        session,
        user_id,
        CALENDAR_READONLY_SCOPE,
    )

    return build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def get_calendar_events(
    session: Session,
    user_id: int,
    start_time: str | None = None,
    end_time: str | None = None,
    calendar_id: str = "primary",
    limit: int = 20,
    days: int = 7,
) -> dict[str, Any]:
    try:
        if limit < 1 or limit > 100:
            return _error("limit must be between 1 and 100.")

        if days < 1 or days > 90:
            return _error("days must be between 1 and 90.")

        service = get_calendar_service(
            session,
            user_id,
        )

        now = datetime.now(timezone.utc)

        start_dt = (
            _parse_datetime(start_time)
            if start_time
            else now
        )

        end_dt = (
            _parse_datetime(end_time)
            if end_time
            else start_dt + timedelta(days=days)
        )

        if end_dt <= start_dt:
            return _error(
                "end_time must be later than start_time."
            )

        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start_dt.astimezone(timezone.utc).isoformat(),
                timeMax=end_dt.astimezone(timezone.utc).isoformat(),
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime",
                showDeleted=False,
            )
            .execute()
        )

        events = [
            _clean_event(event)
            for event in response.get("items", [])
        ]

        return {
            "success": True,
            "calendar_id": calendar_id,
            "count": len(events),
            "events": events,
        }

    except HttpError as exc:
        return _error(
            f"Google Calendar API error: {exc}"
        )

    except Exception as exc:
        return _error(
            f"Calendar error: {exc}"
        )


def find_free_slot(
    session: Session,
    user_id: int,
    start_time: str,
    end_time: str,
    duration_minutes: int = 30,
    calendar_id: str = "primary",
    timezone_name: str = "UTC",
) -> dict[str, Any]:
    try:
        if duration_minutes < 5:
            return _error(
                "duration_minutes must be at least 5."
            )

        window_start = _parse_datetime(
            start_time,
            timezone_name,
        )
        window_end = _parse_datetime(
            end_time,
            timezone_name,
        )

        if window_end <= window_start:
            return _error(
                "end_time must be later than start_time."
            )

        events_result = get_calendar_events(
            session=session,
            user_id=user_id,
            start_time=window_start.isoformat(),
            end_time=window_end.isoformat(),
            calendar_id=calendar_id,
            limit=100,
        )

        if not events_result.get("success"):
            return events_result

        busy: list[tuple[datetime, datetime]] = []

        for event in events_result.get("events", []):
            event_start = event.get("start")
            event_end = event.get("end")

            if not event_start or not event_end:
                continue

            try:
                busy_start = _parse_datetime(
                    event_start,
                    timezone_name,
                )
                busy_end = _parse_datetime(
                    event_end,
                    timezone_name,
                )
            except ValueError:
                continue

            busy.append((busy_start, busy_end))

        busy.sort(key=lambda item: item[0])

        candidate = window_start
        duration = timedelta(minutes=duration_minutes)

        for busy_start, busy_end in busy:
            if candidate + duration <= busy_start:
                return {
                    "success": True,
                    "available": True,
                    "start_time": candidate.isoformat(),
                    "end_time": (
                        candidate + duration
                    ).isoformat(),
                }

            if busy_end > candidate:
                candidate = busy_end

        if candidate + duration <= window_end:
            return {
                "success": True,
                "available": True,
                "start_time": candidate.isoformat(),
                "end_time": (
                    candidate + duration
                ).isoformat(),
            }

        return {
            "success": True,
            "available": False,
            "message": "No free slot was found in the requested window.",
        }

    except Exception as exc:
        return _error(
            f"Free-slot search failed: {exc}"
        )


def create_calendar_event(
    session: Session,
    user_id: int,
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
    timezone_name: str = "UTC",
) -> dict[str, Any]:
    try:
        if not summary.strip():
            return _error("Event summary is required.")

        start_dt = _parse_datetime(
            start_time,
            timezone_name,
        )

        end_dt = _parse_datetime(
            end_time,
            timezone_name,
        )

        if end_dt <= start_dt:
            return _error(
                "end_time must be later than start_time."
            )

        credentials = _get_calendar_credentials(
            session,
            user_id,
            CALENDAR_EVENTS_SCOPE,
        )

        service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

        body: dict[str, Any] = {
            "summary": summary.strip(),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": timezone_name,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": timezone_name,
            },
        }

        if description and description.strip():
            body["description"] = description.strip()

        if location and location.strip():
            body["location"] = location.strip()

        event = (
            service.events()
            .insert(
                calendarId=calendar_id,
                body=body,
            )
            .execute()
        )

        return {
            "success": True,
            "calendar_id": calendar_id,
            "event": _clean_event(event),
        }

    except HttpError as exc:
        return _error(
            f"Google Calendar API error: {exc}"
        )

    except Exception as exc:
        return _error(
            f"Calendar error: {exc}"
        )


def update_calendar_event(
    session: Session,
    user_id: int,
    event_id: str,
    summary: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    description: str | None = None,
    location: str | None = None,
    calendar_id: str = "primary",
    timezone_name: str = "UTC",
) -> dict[str, Any]:
    try:
        credentials = _get_calendar_credentials(
            session,
            user_id,
            CALENDAR_EVENTS_SCOPE,
        )

        service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

        existing = (
            service.events()
            .get(
                calendarId=calendar_id,
                eventId=event_id,
            )
            .execute()
        )

        if summary is not None:
            existing["summary"] = summary.strip()

        if description is not None:
            existing["description"] = description.strip()

        if location is not None:
            existing["location"] = location.strip()

        if start_time is not None:
            existing["start"] = {
                "dateTime": _parse_datetime(
                    start_time,
                    timezone_name,
                ).isoformat(),
                "timeZone": timezone_name,
            }

        if end_time is not None:
            existing["end"] = {
                "dateTime": _parse_datetime(
                    end_time,
                    timezone_name,
                ).isoformat(),
                "timeZone": timezone_name,
            }

        start_value = existing.get("start", {}).get("dateTime")
        end_value = existing.get("end", {}).get("dateTime")

        if start_value and end_value:
            if _parse_datetime(start_value) >= _parse_datetime(end_value):
                return _error(
                    "end_time must be later than start_time."
                )

        updated = (
            service.events()
            .update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing,
            )
            .execute()
        )

        return {
            "success": True,
            "calendar_id": calendar_id,
            "event": _clean_event(updated),
        }

    except HttpError as exc:
        return _error(
            f"Google Calendar API error: {exc}"
        )

    except Exception as exc:
        return _error(
            f"Calendar update failed: {exc}"
        )


def delete_calendar_event(
    session: Session,
    user_id: int,
    event_id: str,
    calendar_id: str = "primary",
) -> dict[str, Any]:
    try:
        credentials = _get_calendar_credentials(
            session,
            user_id,
            CALENDAR_EVENTS_SCOPE,
        )

        service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
        ).execute()

        return {
            "success": True,
            "calendar_id": calendar_id,
            "event_id": event_id,
            "deleted": True,
        }

    except HttpError as exc:
        return _error(
            f"Google Calendar API error: {exc}"
        )

    except Exception as exc:
        return _error(
            f"Calendar delete failed: {exc}"
        )