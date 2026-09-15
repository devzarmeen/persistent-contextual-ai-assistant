from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlmodel import Session

from app.database import get_session
from app.services.auth import get_current_user, security
from app.verification.services import (
    approve_action,
    create_pending_action,
    execute_approved_action,
    get_action,
    list_actions,
    reject_action,
)


router = APIRouter(
    prefix="/api/verification",
    tags=["Verification"],
)


class CreateVerificationActionRequest(BaseModel):
    tool_name: Literal[
        "send_email",
        "create_calendar_event",
    ]
    arguments: dict


def _get_authenticated_user(
    credentials: HTTPAuthorizationCredentials,
    session: Session,
):
    return get_current_user(
        credentials,
        session,
    )


def _serialize_action(action) -> dict:
    return {
        "id": action.id,
        "user_id": action.user_id,
        "tool_name": action.tool_name,
        "action_type": action.action_type,
        "request": action.request,
        "status": action.status,
        "result": action.result,
        "evidence": action.evidence,
        "error": action.error,
        "created_at": action.created_at,
        "approved_at": action.approved_at,
        "rejected_at": action.rejected_at,
        "executing_at": action.executing_at,
        "completed_at": action.completed_at,
    }


@router.post("/actions")
def create_action(
    request: CreateVerificationActionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    """
    Create a new PENDING verification action.

    This endpoint does NOT execute the external action.
    It only creates an approval request.
    """

    user = _get_authenticated_user(
        credentials,
        session,
    )

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is missing.",
        )

    try:
        action = create_pending_action(
            session=session,
            user_id=user.id,
            tool_name=request.tool_name,
            arguments=request.arguments,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "action": _serialize_action(action),
    }


@router.get("/actions")
def get_actions(
    status_filter: str | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    """
    Return verification actions belonging only to the
    authenticated user.
    """

    user = _get_authenticated_user(
        credentials,
        session,
    )

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is missing.",
        )

    actions = list_actions(
        session=session,
        user_id=user.id,
        status=status_filter,
    )

    return {
        "success": True,
        "count": len(actions),
        "actions": [
            _serialize_action(action)
            for action in actions
        ],
    }


@router.get("/actions/{action_id}")
def get_action_details(
    action_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    """
    Return one verification action.

    User ownership is enforced inside get_action().
    """

    user = _get_authenticated_user(
        credentials,
        session,
    )

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is missing.",
        )

    action = get_action(
        session=session,
        user_id=user.id,
        action_id=action_id,
    )

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification action not found.",
        )

    return {
        "success": True,
        "action": _serialize_action(action),
    }


@router.post("/actions/{action_id}/approve")
def approve(
    action_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    """
    Approve a PENDING verification action.

    Approval itself does NOT execute the action.
    """

    user = _get_authenticated_user(
        credentials,
        session,
    )

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is missing.",
        )

    try:
        action = approve_action(
            session=session,
            user_id=user.id,
            action_id=action_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "message": "Verification action approved.",
        "action": _serialize_action(action),
    }


@router.post("/actions/{action_id}/reject")
def reject(
    action_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    """
    Reject a PENDING verification action.
    """

    user = _get_authenticated_user(
        credentials,
        session,
    )

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is missing.",
        )

    try:
        action = reject_action(
            session=session,
            user_id=user.id,
            action_id=action_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "message": "Verification action rejected.",
        "action": _serialize_action(action),
    }


@router.post("/actions/{action_id}/execute")
def execute(
    action_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    """
    Execute an APPROVED action.

    The service changes the action to EXECUTING before
    calling Gmail/Calendar and then verifies the result.
    """

    user = _get_authenticated_user(
        credentials,
        session,
    )

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is missing.",
        )

    try:
        action = execute_approved_action(
            session=session,
            user_id=user.id,
            action_id=action_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if action.status == "FAILED":
        return {
            "success": False,
            "message": "Approved action execution failed.",
            "action": _serialize_action(action),
        }

    return {
        "success": True,
        "message": "Approved action executed and verified.",
        "action": _serialize_action(action),
    }