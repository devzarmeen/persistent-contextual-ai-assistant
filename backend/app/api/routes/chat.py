from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
)
from sqlmodel import Session, select

from app.agents.agent import run_agent
from app.database import get_session
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    AgentMetadata,
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)
from app.services.auth import (
    get_current_user,
    security,
)
from app.services.chat import (
    get_or_create_conversation,
    get_recent_messages,
    process_long_term_memory,
    save_assistant_message,
    save_user_message,
    touch_conversation,
    update_conversation_title,
)


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials,
    session: Session,
):
    return get_current_user(
        credentials,
        session,
    )


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    user = get_authenticated_user(
        credentials,
        session,
    )

    conversation = get_or_create_conversation(
        session=session,
        user_id=user.id,
        conversation_id=request.conversation_id,
    )

    previous_messages = get_recent_messages(
        session=session,
        conversation_id=conversation.id,
        limit=20,
    )

    user_message = save_user_message(
        session=session,
        conversation_id=conversation.id,
        content=request.message,
    )

    update_conversation_title(
        conversation,
        request.message,
    )

    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    agent_metadata = None

    try:
        agent_result = run_agent(
            session=session,
            user_id=user.id,
            user_message=request.message,
            conversation_history=previous_messages,
            attached_document_id=request.document_id,
        )
        
        raw_agent_metadata = agent_result.get(
            "agent"
        )

        if isinstance(
            raw_agent_metadata,
            dict,
        ):
            agent_metadata = AgentMetadata(
                action=raw_agent_metadata.get(
                    "action"
                ),
                tool_name=raw_agent_metadata.get(
                    "tool_name"
                ),
                status=raw_agent_metadata.get(
                    "status"
                ),
                verification_required=bool(
                    raw_agent_metadata.get(
                        "verification_required",
                        False,
                    )
                ),
                verification_action_id=(
                    raw_agent_metadata.get(
                        "verification_action_id"
                    )
                ),
                verification_status=(
                    raw_agent_metadata.get(
                        "verification_status"
                    )
                ),
            )

        if agent_result.get("success"):

            assistant_response = agent_result.get(
                "answer",
                "",
            )

            if not assistant_response:

                assistant_response = (
                    "I could not generate a response "
                    "for your request."
                )

        else:

            assistant_response = agent_result.get(
                "answer",
                (
                    "I could not process your request "
                    "right now."
                ),
            )

            print(
                "Agent execution was not successful. "
                f"Details: {agent_result}"
            )

    except Exception as exc:

        assistant_response = (
            "I could not generate an AI response "
            "right now. Your message has still "
            "been saved successfully."
        )

        agent_metadata = AgentMetadata(
            action=None,
            tool_name=None,
            status="FAILED",
            verification_required=False,
            verification_action_id=None,
            verification_status=None,
        )

        print(
            "Agent execution error: "
            f"{type(exc).__name__}: {exc}"
        )

    assistant_message = save_assistant_message(
        session=session,
        conversation_id=conversation.id,
        content=assistant_response,
    )

    touch_conversation(
        session,
        conversation,
    )

    try:

        process_long_term_memory(
            session=session,
            user_id=user.id,
            user_message=user_message,
        )

    except Exception as exc:

        print(
            "Long-term memory processing error: "
            f"{type(exc).__name__}: {exc}"
        )

    return ChatResponse(
        conversation_id=conversation.id,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        response=assistant_response,
        created_at=assistant_message.created_at,
        agent=agent_metadata,
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def list_conversations(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    user = get_authenticated_user(
        credentials,
        session,
    )

    statement = (
        select(Conversation)
        .where(
            Conversation.user_id == user.id
        )
        .order_by(
            Conversation.updated_at.desc()
        )
    )

    conversations = list(
        session.exec(statement)
    )

    return [
        ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        for conversation in conversations
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation(
    conversation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    user = get_authenticated_user(
        credentials,
        session,
    )

    conversation = session.get(
        Conversation,
        conversation_id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    if conversation.user_id != user.id:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access to "
                "this conversation"
            ),
        )

    statement = (
        select(Message)
        .where(
            Message.conversation_id
            == conversation.id
        )
        .order_by(
            Message.created_at.asc()
        )
    )

    messages = list(
        session.exec(statement)
    )

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in messages
        ],
    )