import json
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.models.verification_action import VerificationAction
from app.services.gmail import get_email, send_email
from app.services.calendar import (
    create_calendar_event,
    delete_calendar_event,
    get_calendar_service,
    update_calendar_event,
)


# ============================================================
# Tools that ALWAYS require human approval
# ============================================================

APPROVAL_REQUIRED_TOOLS = {
    "send_email",
    "create_calendar_event",
    "update_calendar_event",
    "delete_calendar_event",
}


def requires_approval(tool_name: str) -> bool:
    """
    Return True when an external write operation must be
    approved by the user before execution.
    """
    return tool_name in APPROVAL_REQUIRED_TOOLS


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json_dumps(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )


def _json_loads(value: str | None) -> Any:
    if not value:
        return None

    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


# ============================================================
# Create pending verification action
# ============================================================

def create_pending_action(
    session: Session,
    user_id: int,
    tool_name: str,
    arguments: dict[str, Any],
) -> VerificationAction:

    if not requires_approval(tool_name):
        raise ValueError(
            f"Tool '{tool_name}' does not require verification."
        )

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be a dictionary."
        )

    # Keep action types explicit for the verification UI.
    if tool_name == "send_email":
        action_type = "email_send"

    elif tool_name == "create_calendar_event":
        action_type = "calendar_event_create"

    elif tool_name == "update_calendar_event":
        action_type = "calendar_event_update"

    elif tool_name == "delete_calendar_event":
        action_type = "calendar_event_delete"

    else:
        action_type = tool_name

    action = VerificationAction(
        user_id=user_id,
        tool_name=tool_name,
        action_type=action_type,
        request=_json_dumps(arguments),
        status="PENDING",
    )

    session.add(action)
    session.commit()
    session.refresh(action)

    return action


# ============================================================
# Get one action
# ============================================================

def get_action(
    session: Session,
    user_id: int,
    action_id: int,
) -> VerificationAction | None:

    statement = select(VerificationAction).where(
        VerificationAction.id == action_id,
        VerificationAction.user_id == user_id,
    )

    return session.exec(statement).first()


# ============================================================
# List actions
# ============================================================

def list_actions(
    session: Session,
    user_id: int,
    status: str | None = None,
) -> list[VerificationAction]:

    statement = select(VerificationAction).where(
        VerificationAction.user_id == user_id
    )

    if status:
        statement = statement.where(
            VerificationAction.status == status
        )

    statement = statement.order_by(
        VerificationAction.created_at.desc()
    )

    return list(session.exec(statement).all())


# ============================================================
# Approve
# ============================================================

def approve_action(
    session: Session,
    user_id: int,
    action_id: int,
) -> VerificationAction:

    action = get_action(
        session=session,
        user_id=user_id,
        action_id=action_id,
    )

    if action is None:
        raise ValueError(
            "Verification action not found."
        )

    if action.status != "PENDING":
        raise ValueError(
            f"Only PENDING actions can be approved. "
            f"Current status: {action.status}"
        )

    action.status = "APPROVED"
    action.approved_at = _now()
    action.error = None

    session.add(action)
    session.commit()
    session.refresh(action)

    return action


# ============================================================
# Reject
# ============================================================

def reject_action(
    session: Session,
    user_id: int,
    action_id: int,
) -> VerificationAction:

    action = get_action(
        session=session,
        user_id=user_id,
        action_id=action_id,
    )

    if action is None:
        raise ValueError(
            "Verification action not found."
        )

    if action.status != "PENDING":
        raise ValueError(
            f"Only PENDING actions can be rejected. "
            f"Current status: {action.status}"
        )

    action.status = "REJECTED"
    action.rejected_at = _now()
    action.completed_at = _now()

    session.add(action)
    session.commit()
    session.refresh(action)

    return action


# ============================================================
# Gmail verification
# ============================================================

def _verify_gmail_send(
    session: Session,
    user_id: int,
    result: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:

    message = result.get("message")

    if not isinstance(message, dict):
        return False, {
            "verified": False,
            "reason": (
                "Gmail response did not contain "
                "a message object."
            ),
        }

    message_id = message.get("id")

    if not message_id:
        return False, {
            "verified": False,
            "reason": (
                "Gmail response did not contain "
                "a message ID."
            ),
        }

    verification = get_email(
        session=session,
        user_id=user_id,
        message_id=str(message_id),
    )

    if not verification.get("success"):
        return False, {
            "verified": False,
            "message_id": message_id,
            "reason": verification.get(
                "error",
                "Unable to retrieve sent Gmail message.",
            ),
        }

    return True, {
        "verified": True,
        "message_id": message_id,
        "evidence": (
            "Sent Gmail message was retrieved successfully."
        ),
    }


# ============================================================
# Calendar creation/update verification
# ============================================================

def _verify_calendar_event(
    session: Session,
    user_id: int,
    result: dict[str, Any],
    calendar_id: str,
) -> tuple[bool, dict[str, Any]]:

    event = result.get("event")

    if not isinstance(event, dict):
        return False, {
            "verified": False,
            "reason": (
                "Calendar response did not contain "
                "an event object."
            ),
        }

    event_id = event.get("id")

    if not event_id:
        return False, {
            "verified": False,
            "reason": (
                "Calendar response did not contain "
                "an event ID."
            ),
        }

    try:
        service = get_calendar_service(
            session=session,
            user_id=user_id,
        )

        fetched_event = (
            service.events()
            .get(
                calendarId=calendar_id,
                eventId=str(event_id),
            )
            .execute()
        )

    except Exception as exc:
        return False, {
            "verified": False,
            "event_id": event_id,
            "reason": (
                f"Calendar verification failed: {exc}"
            ),
        }

    if not fetched_event or not fetched_event.get("id"):
        return False, {
            "verified": False,
            "event_id": event_id,
            "reason": (
                "Calendar event could not be retrieved."
            ),
        }

    return True, {
        "verified": True,
        "event_id": fetched_event.get("id"),
        "calendar_id": calendar_id,
        "summary": fetched_event.get("summary"),
        "status": fetched_event.get("status"),
        "evidence": (
            "Calendar event was retrieved successfully "
            "after the write operation."
        ),
    }


# ============================================================
# Calendar deletion verification
# ============================================================

def _verify_calendar_event_deleted(
    session: Session,
    user_id: int,
    event_id: str,
    calendar_id: str,
) -> tuple[bool, dict[str, Any]]:

    try:
        service = get_calendar_service(
            session=session,
            user_id=user_id,
        )

        service.events().get(
            calendarId=calendar_id,
            eventId=str(event_id),
        ).execute()

        # Event still exists.
        return False, {
            "verified": False,
            "event_id": event_id,
            "calendar_id": calendar_id,
            "reason": (
                "Calendar event still exists after "
                "the deletion operation."
            ),
        }

    except Exception as exc:
        # Google Calendar normally returns an HTTP 404
        # when the event no longer exists.
        status_code = getattr(
            getattr(exc, "resp", None),
            "status",
            None,
        )

        if status_code == 404:
            return True, {
                "verified": True,
                "event_id": event_id,
                "calendar_id": calendar_id,
                "evidence": (
                    "Calendar event could not be retrieved "
                    "after deletion."
                ),
            }

        return False, {
            "verified": False,
            "event_id": event_id,
            "calendar_id": calendar_id,
            "reason": (
                f"Calendar deletion verification failed: {exc}"
            ),
        }


# ============================================================
# Execute approved external action
# ============================================================

def _execute_approved_action(
    session: Session,
    user_id: int,
    action: VerificationAction,
) -> dict[str, Any]:

    arguments = _json_loads(action.request)

    if not isinstance(arguments, dict):
        raise ValueError(
            "Stored action request is invalid."
        )

    # ========================================================
    # SEND EMAIL
    # ========================================================

    if action.tool_name == "send_email":

        result = send_email(
            session=session,
            user_id=user_id,
            to=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"],
        )

        if not result.get("success"):
            raise RuntimeError(
                result.get(
                    "error",
                    "Gmail send operation failed.",
                )
            )

        verified, evidence = _verify_gmail_send(
            session=session,
            user_id=user_id,
            result=result,
        )

        if not verified:
            raise RuntimeError(
                evidence.get(
                    "reason",
                    "Gmail action could not be verified.",
                )
            )

        return {
            "operation": result,
            "verification": evidence,
        }

    # ========================================================
    # CREATE CALENDAR EVENT
    # ========================================================

    if action.tool_name == "create_calendar_event":

        calendar_id = arguments.get(
            "calendar_id",
            "primary",
        )

        result = create_calendar_event(
            session=session,
            user_id=user_id,
            summary=arguments["summary"],
            start_time=arguments["start_time"],
            end_time=arguments["end_time"],
            description=arguments.get("description"),
            location=arguments.get("location"),
            calendar_id=calendar_id,
            timezone_name=arguments.get(
                "time_zone",
                "UTC",
            ),
        )

        if not result.get("success"):
            raise RuntimeError(
                result.get(
                    "error",
                    "Calendar event creation failed.",
                )
            )

        verified, evidence = _verify_calendar_event(
            session=session,
            user_id=user_id,
            result=result,
            calendar_id=calendar_id,
        )

        if not verified:
            raise RuntimeError(
                evidence.get(
                    "reason",
                    "Calendar event could not be verified.",
                )
            )

        return {
            "operation": result,
            "verification": evidence,
        }

    # ========================================================
    # UPDATE CALENDAR EVENT
    # ========================================================

    if action.tool_name == "update_calendar_event":

        calendar_id = arguments.get(
            "calendar_id",
            "primary",
        )

        event_id = arguments["event_id"]

        result = update_calendar_event(
            session=session,
            user_id=user_id,
            event_id=event_id,
            summary=arguments.get("summary"),
            start_time=arguments.get("start_time"),
            end_time=arguments.get("end_time"),
            description=arguments.get("description"),
            location=arguments.get("location"),
            calendar_id=calendar_id,
            timezone_name=arguments.get(
                "time_zone",
                "UTC",
            ),
        )

        if not result.get("success"):
            raise RuntimeError(
                result.get(
                    "error",
                    "Calendar event update failed.",
                )
            )

        verified, evidence = _verify_calendar_event(
            session=session,
            user_id=user_id,
            result=result,
            calendar_id=calendar_id,
        )

        if not verified:
            raise RuntimeError(
                evidence.get(
                    "reason",
                    "Calendar update could not be verified.",
                )
            )

        return {
            "operation": result,
            "verification": evidence,
        }

    # ========================================================
    # DELETE CALENDAR EVENT
    # ========================================================

    if action.tool_name == "delete_calendar_event":

        calendar_id = arguments.get(
            "calendar_id",
            "primary",
        )

        event_id = arguments["event_id"]

        result = delete_calendar_event(
            session=session,
            user_id=user_id,
            event_id=event_id,
            calendar_id=calendar_id,
        )

        if not result.get("success"):
            raise RuntimeError(
                result.get(
                    "error",
                    "Calendar event deletion failed.",
                )
            )

        verified, evidence = _verify_calendar_event_deleted(
            session=session,
            user_id=user_id,
            event_id=event_id,
            calendar_id=calendar_id,
        )

        if not verified:
            raise RuntimeError(
                evidence.get(
                    "reason",
                    "Calendar deletion could not be verified.",
                )
            )

        return {
            "operation": result,
            "verification": evidence,
        }

    # ========================================================
    # Unknown verification tool
    # ========================================================

    raise ValueError(
        f"Unsupported verification tool: {action.tool_name}"
    )


# ============================================================
# Execute APPROVED action
# ============================================================

def execute_approved_action(
    session: Session,
    user_id: int,
    action_id: int,
) -> VerificationAction:

    action = get_action(
        session=session,
        user_id=user_id,
        action_id=action_id,
    )

    if action is None:
        raise ValueError(
            "Verification action not found."
        )

    if action.status != "APPROVED":
        raise ValueError(
            f"Only APPROVED actions can be executed. "
            f"Current status: {action.status}"
        )

    # IMPORTANT:
    # Mark the action as EXECUTING before calling
    # Gmail / Google Calendar.
    #
    # This prevents normal API calls from executing
    # the same APPROVED action twice.
    action.status = "EXECUTING"
    action.executing_at = _now()
    action.error = None

    session.add(action)
    session.commit()
    session.refresh(action)

    try:

        result = _execute_approved_action(
            session=session,
            user_id=user_id,
            action=action,
        )

        action.result = _json_dumps(result)

        evidence = result.get(
            "verification"
        )

        action.evidence = _json_dumps(
            evidence
        )

        action.status = "VERIFIED"
        action.completed_at = _now()

        session.add(action)
        session.commit()
        session.refresh(action)

        return action

    except Exception as exc:

        action.status = "FAILED"
        action.error = str(exc)
        action.completed_at = _now()

        action.evidence = _json_dumps(
            {
                "verified": False,
                "error": str(exc),
            }
        )

        session.add(action)
        session.commit()
        session.refresh(action)

        return action