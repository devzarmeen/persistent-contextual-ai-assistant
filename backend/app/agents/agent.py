import time
from typing import Any

from google import genai
from google.genai import errors
from google.genai import types
from sqlmodel import Session

from app.agents.decision import decide_next_action
from app.agents.models import AgentDecision
from app.agents.runner import run_tool
from app.config import settings
from app.models.message import Message
from app.verification.services import requires_approval


# ============================================================
# GEMINI MODEL CONFIGURATION
# ============================================================

PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

MAX_TEMPORARY_RETRIES = 2

TEMPORARY_SERVER_CODES = {
    500,
    502,
    503,
    504,
}


# ============================================================
# FINAL ANSWER SYSTEM INSTRUCTION
# ============================================================

FINAL_ANSWER_SYSTEM_INSTRUCTION = """
You are the final-answer component of a persistent contextual
AI assistant called ContextAI.

Your job is to produce a clear, accurate, useful response to
the user's request using:

1. The user's current message.
2. Recent conversation history.
3. The result returned by the ContextAI tool.

IMPORTANT RULES
===============

- Answer the user's actual question.
- Use the tool result as the source of truth for retrieved
  information.
- Do not invent information that is not present in the tool
  result or conversation context.
- Do not expose internal agent reasoning.
- Do not mention model selection, fallback models, quotas,
  API errors, or internal implementation details.
- If the tool returned no useful information, say so clearly.
- If the tool result contains several relevant memories,
  summarize them naturally.
- Keep the answer concise but useful.
- Use readable formatting when appropriate.
- Do not claim an external action happened unless the tool
  result confirms that it actually happened.
- For pending verification actions, clearly explain that
  human approval is required.
"""


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def _extract_text(response: Any) -> str:
    text = getattr(response, "text", None)

    if text:
        return text.strip()

    return ""


def format_conversation_history(
    messages: list[Message],
) -> str:

    if not messages:
        return "No previous conversation messages."

    lines: list[str] = []

    for message in messages:

        role = message.role.strip().lower()

        if role == "user":
            speaker = "User"

        elif role == "assistant":
            speaker = "Assistant"

        elif role == "system":
            speaker = "System"

        else:
            speaker = role.capitalize()

        content = message.content.strip()

        if content:
            lines.append(
                f"{speaker}: {content}"
            )

    if not lines:
        return "No previous conversation messages."

    return "\n".join(lines)


# ============================================================
# ERROR HELPERS
# ============================================================

def _get_status_code(
    exc: Exception,
) -> int | None:

    status_code = getattr(
        exc,
        "code",
        None,
    )

    if isinstance(status_code, int):
        return status_code

    return None


def _is_quota_error(
    exc: Exception,
) -> bool:

    status_code = _get_status_code(exc)

    if status_code == 429:
        return True

    message = str(exc).lower()

    quota_keywords = [
        "quota",
        "resource_exhausted",
        "free_tier",
        "quota exceeded",
    ]

    return any(
        keyword in message
        for keyword in quota_keywords
    )


def _is_temporary_server_error(
    exc: Exception,
) -> bool:

    status_code = _get_status_code(exc)

    return status_code in TEMPORARY_SERVER_CODES


# ============================================================
# FINAL ANSWER GENERATION
# ============================================================

def _generate_final_answer_with_model(
    client: genai.Client,
    model: str,
    prompt: str,
) -> str:

    for attempt in range(
        1,
        MAX_TEMPORARY_RETRIES + 1,
    ):

        try:

            print(
                f"Gemini final-answer request: "
                f"model={model}, "
                f"attempt={attempt}/"
                f"{MAX_TEMPORARY_RETRIES}"
            )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                ),
            )

            answer = _extract_text(response)

            if not answer:
                raise RuntimeError(
                    f"Gemini returned an empty final answer "
                    f"using model {model}."
                )

            print(
                f"Gemini final-answer successful: "
                f"model={model}"
            )

            return answer

        except errors.ServerError as exc:

            status_code = _get_status_code(exc)

            print(
                f"Gemini final-answer server error: "
                f"model={model}, "
                f"status={status_code}, "
                f"attempt={attempt}/"
                f"{MAX_TEMPORARY_RETRIES}"
            )

            if (
                _is_temporary_server_error(exc)
                and attempt < MAX_TEMPORARY_RETRIES
            ):

                wait_seconds = 2 ** (attempt - 1)

                print(
                    f"Retrying final answer with "
                    f"{model} in {wait_seconds}s..."
                )

                time.sleep(wait_seconds)

                continue

            raise RuntimeError(
                f"Gemini final-answer model {model} "
                f"failed after {attempt} attempts: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        except errors.APIError as exc:

            status_code = _get_status_code(exc)

            if _is_quota_error(exc):

                print(
                    f"Gemini final-answer quota exhausted: "
                    f"model={model}, "
                    f"status={status_code}"
                )

                raise RuntimeError(
                    f"Gemini final-answer quota exhausted "
                    f"for {model}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if (
                _is_temporary_server_error(exc)
                and attempt < MAX_TEMPORARY_RETRIES
            ):

                wait_seconds = 2 ** (attempt - 1)

                print(
                    f"Gemini temporary final-answer error: "
                    f"model={model}, "
                    f"status={status_code}"
                )

                print(
                    f"Retrying final answer with "
                    f"{model} in {wait_seconds}s..."
                )

                time.sleep(wait_seconds)

                continue

            raise RuntimeError(
                f"Gemini final-answer API error for "
                f"{model}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        except RuntimeError:
            raise

        except Exception as exc:

            raise RuntimeError(
                f"Gemini final-answer request failed "
                f"for {model}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    raise RuntimeError(
        f"Gemini final-answer model {model} failed."
    )


def generate_final_answer(
    user_message: str,
    tool_name: str,
    tool_result: dict[str, Any],
    conversation_history: str,
) -> str:

    client = get_gemini_client()

    prompt = f"""
{FINAL_ANSWER_SYSTEM_INSTRUCTION}

RECENT CONVERSATION HISTORY
============================

{conversation_history}


CURRENT USER MESSAGE
====================

{user_message}


TOOL USED
=========

{tool_name}


TOOL RESULT
===========

{tool_result}


TASK
====

Generate the final response to the user.

Use the tool result as factual evidence.

Do not mention internal implementation details.

Do not mention Gemini.

Do not mention quotas or API errors.

Answer naturally as ContextAI.
"""

    model_chain = [
        PRIMARY_MODEL,
        *FALLBACK_MODELS,
    ]

    last_error: Exception | None = None

    for index, model in enumerate(model_chain):

        try:

            answer = _generate_final_answer_with_model(
                client=client,
                model=model,
                prompt=prompt,
            )

            if index == 0:

                print(
                    f"Primary final-answer model succeeded: "
                    f"{model}"
                )

            else:

                print(
                    f"Fallback final-answer model succeeded: "
                    f"{model}"
                )

            return answer

        except Exception as exc:

            last_error = exc

            print(
                f"Final-answer model unavailable: "
                f"{model} -> "
                f"{type(exc).__name__}: {exc}"
            )

            if index < len(model_chain) - 1:

                next_model = model_chain[index + 1]

                print(
                    f"Switching final-answer model "
                    f"from {model} "
                    f"to {next_model}..."
                )

    if last_error is not None:

        raise RuntimeError(
            "All Gemini final-answer models failed. "
            f"Model chain={model_chain}. "
            f"Last error: "
            f"{type(last_error).__name__}: "
            f"{last_error}"
        ) from last_error

    raise RuntimeError(
        "Gemini final-answer generation failed "
        "unexpectedly."
    )


# ============================================================
# FRONTEND-FRIENDLY AGENT METADATA
# ============================================================

def _build_agent_metadata(
    decision: AgentDecision | None,
    tool_result: dict[str, Any] | None,
) -> dict[str, Any]:

    if decision is None:
        return {
            "action": None,
            "tool_name": None,
            "status": "FAILED",
            "verification_required": False,
            "verification_action_id": None,
            "verification_status": None,
        }

    tool_name = None

    if decision.tool_call is not None:
        tool_name = decision.tool_call.tool_name

    verification_required = False
    verification_action_id = None
    verification_status = None

    if isinstance(tool_result, dict):

        verification_required = bool(
            tool_result.get(
                "verification_required",
                False,
            )
        )

        verification_action_id = tool_result.get(
            "verification_action_id"
        )

        verification_status = tool_result.get(
            "verification_status"
        )

        data = tool_result.get("data")

        if isinstance(data, dict):

            if verification_action_id is None:
                verification_action_id = data.get(
                    "action_id"
                )

            if verification_status is None:
                verification_status = data.get(
                    "status"
                )

    if decision.action == "final_answer":

        status = "COMPLETED"

    elif verification_required:

        status = (
            verification_status
            or "PENDING"
        )

    elif tool_result is not None:

        status = (
            "COMPLETED"
            if tool_result.get("success")
            else "FAILED"
        )

    else:

        status = "PENDING"

    return {
        "action": decision.action,
        "tool_name": tool_name,
        "status": status,
        "verification_required": verification_required,
        "verification_action_id": (
            verification_action_id
        ),
        "verification_status": (
            verification_status
        ),
    }


# ============================================================
# VERIFICATION PENDING RESPONSE
# ============================================================

def _verification_pending_response(
    decision: AgentDecision,
    tool_result: dict[str, Any],
) -> dict[str, Any]:

    tool_call = decision.tool_call

    if tool_call is None:

        return {
            "success": False,
            "answer": (
                "The action requires verification, "
                "but no valid tool call was provided."
            ),
            "decision": decision.model_dump(
                mode="json"
            ),
            "tool_result": tool_result,
            "verification_required": True,
            "verification_action_id": None,
            "verification_status": "PENDING",
            "agent": _build_agent_metadata(
                decision,
                tool_result,
            ),
        }

    data = tool_result.get("data")

    if not isinstance(data, dict):
        data = {}

    action_id = data.get(
        "action_id"
    )

    verification_status = data.get(
        "status",
        "PENDING",
    )

    if tool_call.tool_name == "send_email":

        action_description = "email"

    elif (
        tool_call.tool_name
        == "create_calendar_event"
    ):

        action_description = "calendar event"

    else:

        action_description = "external action"

    answer = (
        f"I've prepared the {action_description}, "
        "but it requires your approval before "
        "anything is sent or created.\n\n"
        f"Verification action ID: {action_id}\n"
        f"Status: {verification_status}"
    )

    return {
        "success": True,
        "answer": answer,
        "decision": decision.model_dump(
            mode="json"
        ),
        "tool_result": tool_result,
        "verification_required": True,
        "verification_action_id": action_id,
        "verification_status": verification_status,
        "agent": _build_agent_metadata(
            decision,
            {
                **tool_result,
                "verification_required": True,
                "verification_action_id": action_id,
                "verification_status": verification_status,
            },
        ),
    }


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(
    session: Session,
    user_id: int,
    user_message: str,
    conversation_history: list[Message] | None = None,
) -> dict[str, Any]:

    user_message = user_message.strip()

    if not user_message:

        return {
            "success": False,
            "answer": "Please provide a message.",
            "decision": None,
            "tool_result": None,
            "agent": {
                "action": None,
                "tool_name": None,
                "status": "FAILED",
                "verification_required": False,
                "verification_action_id": None,
                "verification_status": None,
            },
        }

    history = conversation_history or []

    conversation_history_text = (
        format_conversation_history(history)
    )

    # ========================================================
    # STEP 1
    # Gemini decides whether to use a tool.
    # ========================================================

    try:

        decision = decide_next_action(
            user_message=user_message,
            conversation_history=(
                conversation_history_text
            ),
        )

    except Exception as exc:

        return {
            "success": False,
            "answer": (
                "I couldn't process your request "
                "right now. Please try again."
            ),
            "decision": None,
            "tool_result": None,
            "error": str(exc),
            "agent": {
                "action": None,
                "tool_name": None,
                "status": "FAILED",
                "verification_required": False,
                "verification_action_id": None,
                "verification_status": None,
            },
        }

    # ========================================================
    # STEP 2
    # Direct final answer
    # ========================================================

    if decision.action == "final_answer":

        return {
            "success": True,
            "answer": _decision_to_final_answer(
                decision
            ),
            "decision": decision.model_dump(
                mode="json"
            ),
            "tool_result": None,
            "agent": _build_agent_metadata(
                decision,
                None,
            ),
        }

    # ========================================================
    # STEP 3
    # Tool action
    # ========================================================

    if decision.action == "tool":

        if decision.tool_call is None:

            return {
                "success": False,
                "answer": (
                    "The agent selected a tool "
                    "but did not provide valid "
                    "tool arguments."
                ),
                "decision": decision.model_dump(
                    mode="json"
                ),
                "tool_result": None,
                "agent": _build_agent_metadata(
                    decision,
                    None,
                ),
            }

        # ====================================================
        # Execute tool / create verification action.
        # ====================================================

        tool_result_model = run_tool(
            session=session,
            user_id=user_id,
            tool_call=decision.tool_call,
        )

        tool_result = tool_result_model.model_dump(
            mode="json"
        )

        # ====================================================
        # External action requiring approval.
        # ====================================================

        if (
            tool_result_model.success
            and requires_approval(
                decision.tool_call.tool_name
            )
        ):

            return _verification_pending_response(
                decision=decision,
                tool_result=tool_result,
            )

        # ====================================================
        # Tool failed.
        # ====================================================

        if not tool_result_model.success:

            return {
                "success": False,
                "answer": (
                    "I couldn't retrieve the "
                    "information needed to answer "
                    "your question."
                ),
                "decision": decision.model_dump(
                    mode="json"
                ),
                "tool_result": tool_result,
                "agent": _build_agent_metadata(
                    decision,
                    tool_result,
                ),
            }

        # ====================================================
        # STEP 4
        # Generate final answer.
        # ====================================================

        try:

            final_answer = generate_final_answer(
                user_message=user_message,
                tool_name=(
                    tool_result_model.tool_name
                ),
                tool_result=tool_result,
                conversation_history=(
                    conversation_history_text
                ),
            )

        except Exception as exc:

            return {
                "success": False,
                "answer": (
                    "The requested information "
                    "was retrieved successfully, "
                    "but I couldn't generate the "
                    "final response right now."
                ),
                "decision": decision.model_dump(
                    mode="json"
                ),
                "tool_result": tool_result,
                "error": str(exc),
                "agent": _build_agent_metadata(
                    decision,
                    tool_result,
                ),
            }

        # ====================================================
        # COMPLETE SUCCESS
        # ====================================================

        return {
            "success": True,
            "answer": final_answer,
            "decision": decision.model_dump(
                mode="json"
            ),
            "tool_result": tool_result,
            "agent": _build_agent_metadata(
                decision,
                tool_result,
            ),
        }

    # ========================================================
    # Unsupported action
    # ========================================================

    return {
        "success": False,
        "answer": (
            "The agent produced an unsupported action."
        ),
        "decision": decision.model_dump(
            mode="json"
        ),
        "tool_result": None,
        "agent": _build_agent_metadata(
            decision,
            None,
        ),
    }


# ============================================================
# DECISION ANSWER HELPER
# ============================================================

def _decision_to_final_answer(
    decision: AgentDecision,
) -> str:

    if decision.answer:
        return decision.answer.strip()

    return (
        "I was unable to generate a final answer "
        "for this request."
    )