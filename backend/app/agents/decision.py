import json
import time
from typing import Any

from google import genai
from google.genai import errors
from google.genai import types

from app.agents.models import (
    AgentDecision,
    CreateCalendarEventArguments,
    DeleteCalendarEventArguments,
    DraftEmailArguments,
    FindFreeSlotArguments,
    GetCalendarEventsArguments,
    GetDocumentArguments,
    GetEmailArguments,
    GetUserContextArguments,
    SaveMemoryArguments,
    SearchDocumentsArguments,
    SearchEmailsArguments,
    SearchMemoryArguments,
    SendEmailArguments,
    ToolArguments,
    UpdateCalendarEventArguments,
)
from app.config import settings


# ============================================================
# GEMINI MODEL CONFIGURATION
# ============================================================

PRIMARY_MODEL = "gemini-3.8-flash"

# Fallback order:
#
#   3.8 Flash
#       ↓
#   3.6 Flash
#       ↓
#   3.5 Flash
#
FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]

# Only temporary availability errors should be retried.
# A quota-exhausted 429 switches immediately to the next model.
RETRYABLE_503_CODES = {
    500,
    502,
    503,
    504,
}

MAX_RETRIES_FOR_TEMPORARY_ERROR = 2


# ============================================================
# AGENT DECISION INSTRUCTIONS
# ============================================================

AGENT_DECISION_INSTRUCTION = """
You are the decision engine of a persistent contextual AI assistant.

Your job is to decide whether the user's CURRENT request should:

1. be answered directly with final_answer, or
2. use exactly ONE available tool.

You must return ONLY valid JSON matching the required
AgentDecision structure.

============================================================
AVAILABLE TOOLS
============================================================

The application currently provides these tools:

1. search_memory
------------------------------------------------------------
Use this when the user asks about remembered personal context,
preferences, decisions, projects, tasks, deadlines, people,
or other durable information stored in memory.

Examples:
- "What do you remember about my project?"
- "What was my previous decision?"
- "What is my preference?"
- "What deadline did I tell you?"

Do not use this for information that is not stored user context.


2. search_documents
------------------------------------------------------------
Use this when the user asks to search uploaded documents.

Examples:
- "Search my documents for the project requirements."
- "What does my uploaded PDF say about authentication?"
- "Find information about X in my documents."


3. get_document
------------------------------------------------------------
Use this when the user refers to a specific document and wants
the document's full content or detailed contents.

Use the document ID when the user provides or when conversation
context contains a valid document ID.

Never invent a document ID.


4. get_user_context
------------------------------------------------------------
Use this when the user asks for a broader summary of what the
assistant knows about them from stored memory.

Examples:
- "What do you know about me?"
- "Give me my saved context."
- "Summarize what you remember about my projects."

This is different from search_memory:

- search_memory = targeted memory retrieval
- get_user_context = broader stored-context overview


5. save_memory
------------------------------------------------------------
Use this ONLY when the user explicitly asks the assistant to
remember or save durable information.

Examples:
- "Remember that my project deadline is September 20."
- "Please remember that I prefer Python."
- "Save this for later."

Do NOT save information merely because the user casually
mentions it.


6. search_emails
------------------------------------------------------------
Use this when the user asks to find, search, locate, list,
or summarize emails from connected Gmail.

Examples:
- "Find my unread emails."
- "Search emails from John."
- "Show me emails about the project."

Do not invent Gmail message IDs.


7. get_email
------------------------------------------------------------
Use this when the user refers to a specific Gmail message and
wants its full content.

Use a real message ID when available.

Never invent a Gmail message ID.


8. draft_email
------------------------------------------------------------
Use this when the user explicitly asks to prepare or draft an
email without sending it.

Examples:
- "Draft an email to Sarah about tomorrow's meeting."
- "Write a reply to this email."
- "Prepare an email asking for the project update."

Do NOT use send_email for draft-only requests.

Do not send the email when the user only asks for a draft.


9. send_email
------------------------------------------------------------
Use this ONLY when the user explicitly asks to send an email.

IMPORTANT:
- Sending email is an external side effect.
- Human verification is required before execution.
- Never invent a recipient.
- Never invent missing email content.
- If required information is missing, use final_answer and
  ask the user for the missing information.
- Do not use this for draft-only requests.


10. get_calendar_events
------------------------------------------------------------
Use this when the user asks about calendar events, meetings,
appointments, schedules, or upcoming events.

Examples:
- "What meetings do I have this week?"
- "What's on my calendar tomorrow?"
- "Show my upcoming events."

Use calendar_id "primary" unless another calendar is specified.

The days argument represents the number of future days to search.


11. find_free_slot
------------------------------------------------------------
Use this when the user asks when they are available or asks the
assistant to find an available time in a calendar window.

Examples:
- "Find me a free 30-minute slot tomorrow."
- "When am I free between 2 and 6 PM?"
- "Find an available hour this afternoon."

This is a read-only calendar operation.

Do not create an event automatically.


12. create_calendar_event
------------------------------------------------------------
Use this when the user explicitly asks to create, schedule, or
add an event to Google Calendar.

IMPORTANT:
- Creating an event is an external side effect.
- Human verification is required before execution.
- Never invent missing event information.
- If title, start time, or end time is missing, use
  final_answer and ask for the missing information.
- Use calendar_id "primary" unless another calendar is specified.
- Use time_zone "Asia/Karachi" when Pakistan time is clearly
  implied and no other timezone is specified.


13. update_calendar_event
------------------------------------------------------------
Use this when the user explicitly asks to modify an existing
calendar event.

Examples:
- "Move my meeting to 4 PM."
- "Change tomorrow's meeting title."
- "Update the location of event X."

IMPORTANT:
- Updating an event is an external side effect.
- Human verification is required before execution.
- Never invent an event ID.
- If a specific event cannot be identified, use final_answer
  and ask for clarification.


14. delete_calendar_event
------------------------------------------------------------
Use this when the user explicitly asks to remove or cancel an
existing calendar event.

IMPORTANT:
- Deleting an event is an external side effect.
- Human verification is required before execution.
- Never invent an event ID.
- If a specific event cannot be identified, use final_answer
  and ask for clarification.


============================================================
EXTERNAL ACTION / APPROVAL RULE
============================================================

The following operations require human approval before the
application actually executes them:

- send_email
- create_calendar_event
- update_calendar_event
- delete_calendar_event

The decision engine must still select the appropriate tool when
the user explicitly requests one of these operations.

The application runner will convert the tool request into a
pending verification action.

Do NOT attempt to execute tools yourself.


============================================================
TOOL SELECTION RULES
============================================================

Choose exactly ONE action.

Use a tool when information must be retrieved from:

- stored memory
- uploaded documents
- Gmail
- Google Calendar

Use a tool when the user explicitly requests a supported action.

Use final_answer when:

- the request can be answered without a tool,
- required information for a tool is missing,
- clarification is necessary,
- the requested operation is unsupported.

Never invent:

- document IDs
- Gmail message IDs
- calendar event IDs
- email addresses
- dates
- times
- event details
- information supposedly stored in memory

Conversation history is context, but it is NOT automatically
verified truth.

If the user asks about a specific external object and the
required identifier is not available, ask for clarification
instead of inventing an identifier.

Do not expose your reasoning process.

Do not return markdown.

Do not return code fences.

Return JSON only.


============================================================
IMPORTANT DISTINCTIONS
============================================================

Memory:
- "What do you remember about X?" → search_memory
- "What do you know about me?" → get_user_context
- "Remember X." → save_memory

Documents:
- "Search my documents for X." → search_documents
- "Show the contents of document 12." → get_document

Email:
- "Find emails about X." → search_emails
- "Show email abc123." → get_email
- "Draft an email..." → draft_email
- "Send this email..." → send_email

Calendar:
- "What meetings do I have?" → get_calendar_events
- "When am I free?" → find_free_slot
- "Schedule a meeting..." → create_calendar_event
- "Move/update my meeting..." → update_calendar_event
- "Cancel/delete my meeting..." → delete_calendar_event


============================================================
FINAL ANSWER FORMAT
============================================================

{
  "action": "final_answer",
  "answer": "..."
}


============================================================
TOOL FORMAT
============================================================

{
  "action": "tool",
  "tool_call": {
    "tool_name": "search_memory",
    "arguments": {
      "query": "...",
      "limit": 5
    }
  }
}

The arguments MUST match the actual schema supplied by the
application.

============================================================
PYDANTIC TOOL SCHEMA
============================================================

The application will provide the authoritative ToolArguments
schemas after these instructions.

Use those schemas for argument names and types.
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
# RESPONSE HELPERS
# ============================================================

def _extract_text(response: Any) -> str:
    text = getattr(response, "text", None)

    if text:
        return text.strip()

    return ""


def _parse_agent_decision(
    text: str,
) -> AgentDecision:
    cleaned = text.strip()

    # Safety handling in case Gemini returns JSON
    # inside markdown code fences.
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        payload = json.loads(cleaned)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON for the agent decision."
        ) from exc

    try:
        return AgentDecision.model_validate(payload)

    except Exception as exc:
        raise RuntimeError(
            "Gemini returned an invalid AgentDecision structure."
        ) from exc


def _agent_decision_schema() -> dict[str, Any]:
    return AgentDecision.model_json_schema()


def _tool_arguments_schema() -> dict[str, Any]:
    """
    Return the authoritative schemas for all supported tool
    argument models.

    ToolArguments is a typing.Union, so it does not itself expose
    model_json_schema(). The individual Pydantic argument models
    provide the authoritative schemas.
    """

    return {
        "SearchMemoryArguments": (
            SearchMemoryArguments.model_json_schema()
        ),
        "SearchDocumentsArguments": (
            SearchDocumentsArguments.model_json_schema()
        ),
        "GetDocumentArguments": (
            GetDocumentArguments.model_json_schema()
        ),
        "GetUserContextArguments": (
            GetUserContextArguments.model_json_schema()
        ),
        "SaveMemoryArguments": (
            SaveMemoryArguments.model_json_schema()
        ),
        "SearchEmailsArguments": (
            SearchEmailsArguments.model_json_schema()
        ),
        "GetEmailArguments": (
            GetEmailArguments.model_json_schema()
        ),
        "DraftEmailArguments": (
            DraftEmailArguments.model_json_schema()
        ),
        "SendEmailArguments": (
            SendEmailArguments.model_json_schema()
        ),
        "GetCalendarEventsArguments": (
            GetCalendarEventsArguments.model_json_schema()
        ),
        "FindFreeSlotArguments": (
            FindFreeSlotArguments.model_json_schema()
        ),
        "CreateCalendarEventArguments": (
            CreateCalendarEventArguments.model_json_schema()
        ),
        "UpdateCalendarEventArguments": (
            UpdateCalendarEventArguments.model_json_schema()
        ),
        "DeleteCalendarEventArguments": (
            DeleteCalendarEventArguments.model_json_schema()
        ),
    }


# ============================================================
# ERROR HELPERS
# ============================================================

def _get_status_code(
    exc: Exception,
) -> int | None:
    status_code = getattr(exc, "code", None)

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

    return status_code in RETRYABLE_503_CODES


# ============================================================
# ONE MODEL REQUEST
# ============================================================

def _request_decision_from_model(
    client: genai.Client,
    model: str,
    prompt: str,
) -> AgentDecision:

    for attempt in range(
        1,
        MAX_RETRIES_FOR_TEMPORARY_ERROR + 1,
    ):

        try:
            print(
                f"Gemini decision request: "
                f"model={model}, "
                f"attempt={attempt}/"
                f"{MAX_RETRIES_FOR_TEMPORARY_ERROR}"
            )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=_agent_decision_schema(),
                ),
            )

            text = _extract_text(response)

            if not text:
                raise RuntimeError(
                    f"Gemini returned an empty response "
                    f"using model {model}."
                )

            decision = _parse_agent_decision(text)

            print(
                f"Gemini decision successful: "
                f"model={model}"
            )

            return decision

        except errors.ServerError as exc:

            status_code = _get_status_code(exc)

            print(
                f"Gemini server error: "
                f"model={model}, "
                f"status={status_code}, "
                f"attempt={attempt}/"
                f"{MAX_RETRIES_FOR_TEMPORARY_ERROR}"
            )

            # Retry temporary 5xx errors.
            if (
                _is_temporary_server_error(exc)
                and attempt
                < MAX_RETRIES_FOR_TEMPORARY_ERROR
            ):

                wait_seconds = 2 ** (attempt - 1)

                print(
                    f"Retrying {model} "
                    f"in {wait_seconds}s..."
                )

                time.sleep(wait_seconds)

                continue

            raise RuntimeError(
                f"Gemini model {model} failed after "
                f"{attempt} attempts: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        except errors.APIError as exc:

            status_code = _get_status_code(exc)

            # 429 quota exhaustion:
            # immediately switch to the next model.
            if _is_quota_error(exc):

                print(
                    f"Gemini quota exhausted: "
                    f"model={model}, "
                    f"status={status_code}"
                )

                raise RuntimeError(
                    f"Gemini quota exhausted for {model}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            # Retry other temporary API errors.
            if (
                _is_temporary_server_error(exc)
                and attempt
                < MAX_RETRIES_FOR_TEMPORARY_ERROR
            ):

                wait_seconds = 2 ** (attempt - 1)

                print(
                    f"Gemini temporary API error: "
                    f"model={model}, "
                    f"status={status_code}"
                )

                print(
                    f"Retrying {model} "
                    f"in {wait_seconds}s..."
                )

                time.sleep(wait_seconds)

                continue

            raise RuntimeError(
                f"Gemini API error for {model}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        except RuntimeError:
            raise

        except Exception as exc:

            raise RuntimeError(
                f"Gemini decision request failed for "
                f"{model}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    raise RuntimeError(
        f"Gemini model {model} failed."
    )


# ============================================================
# MAIN DECISION ENGINE
# ============================================================

def decide_next_action(
    user_message: str,
    conversation_history: str = "",
) -> AgentDecision:

    """
    Decide whether the current user request should be answered
    directly or handled through one ContextAI tool.

    MODEL FALLBACK:

        gemini-3.8-flash
                ↓
        gemini-3.6-flash
                ↓
        gemini-3.5-flash

    Behavior:

        429 quota error
            -> immediately switch model

        503 / temporary 5xx
            -> retry current model
            -> then switch model

        successful response
            -> return validated AgentDecision
    """

    user_message = user_message.strip()

    if not user_message:
        raise ValueError(
            "User message cannot be empty."
        )

    if not conversation_history.strip():
        conversation_history = (
            "No previous conversation messages."
        )

    client = get_gemini_client()

    tool_schema = json.dumps(
        _tool_arguments_schema(),
        indent=2,
        default=str,
    )

    prompt = f"""
{AGENT_DECISION_INSTRUCTION}

============================================================
AUTHORITATIVE TOOL ARGUMENT SCHEMAS
============================================================

{tool_schema}

============================================================
RECENT CONVERSATION HISTORY
============================================================

{conversation_history}

============================================================
CURRENT USER MESSAGE
============================================================

{user_message}

============================================================
FINAL DECISION
============================================================

Decide the single best next action for the CURRENT USER MESSAGE.

IMPORTANT:
- Return exactly one action.
- If a tool is required, return exactly one tool call.
- Do not execute the tool yourself.
- Do not explain your decision.
- Do not expose reasoning.
- Do not invent identifiers or missing information.
- Return JSON only.
"""

    model_chain = [
        PRIMARY_MODEL,
        *FALLBACK_MODELS,
    ]

    last_error: Exception | None = None

    for index, model in enumerate(model_chain):

        try:

            decision = _request_decision_from_model(
                client=client,
                model=model,
                prompt=prompt,
            )

            if index == 0:

                print(
                    f"Primary Gemini model succeeded: "
                    f"{model}"
                )

            else:

                print(
                    f"Fallback Gemini model succeeded: "
                    f"{model}"
                )

            return decision

        except Exception as exc:

            last_error = exc

            print(
                f"Gemini model unavailable: "
                f"{model} -> "
                f"{type(exc).__name__}: {exc}"
            )

            if index < len(model_chain) - 1:

                next_model = model_chain[index + 1]

                print(
                    f"Switching from {model} "
                    f"to fallback model "
                    f"{next_model}..."
                )

    # --------------------------------------------------------
    # All models failed.
    # --------------------------------------------------------

    if last_error is not None:

        raise RuntimeError(
            "All Gemini decision models failed. "
            f"Model chain={model_chain}. "
            f"Last error: "
            f"{type(last_error).__name__}: "
            f"{last_error}"
        ) from last_error

    raise RuntimeError(
        "Gemini decision engine failed unexpectedly."
    )