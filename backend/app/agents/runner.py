from sqlmodel import Session

from app.agents.models import ToolCall, ToolResult
from app.agents.tools import execute_tool
from app.verification.services import (
    create_pending_action,
    requires_approval,
)


def run_tool(
    session: Session,
    user_id: int,
    tool_call: ToolCall,
) -> ToolResult:
    """
    Execute one agent tool safely.

    External write operations are intercepted and converted
    into PENDING verification actions. They are NEVER executed
    directly by the agent.
    """

    tool_name = tool_call.tool_name

    # ---------------------------------------------------------
    # Phase 9 Human-in-the-Loop Security Gate
    #
    # External write actions:
    #   - send_email
    #   - create_calendar_event
    #   - update_calendar_event
    #   - delete_calendar_event
    #
    # are converted into PENDING actions.
    # Actual execution happens only after:
    #
    # PENDING -> APPROVED -> EXECUTING -> VERIFIED
    #
    # ---------------------------------------------------------
    if requires_approval(tool_name):
        arguments = tool_call.arguments.model_dump()

        action = create_pending_action(
            session=session,
            user_id=user_id,
            tool_name=tool_name,
            arguments=arguments,
        )

        return ToolResult(
            tool_name=tool_name,
            success=True,
            data={
                "verification_required": True,
                "status": action.status,
                "action_id": action.id,
                "tool_name": action.tool_name,
                "action_type": action.action_type,
                "message": (
                    "This external action requires human approval "
                    "before execution."
                ),
            },
        )

    # ---------------------------------------------------------
    # Read-only / internal tools
    # ---------------------------------------------------------
    result = execute_tool(
        session=session,
        user_id=user_id,
        tool_name=tool_name,
        arguments=tool_call.arguments,
    )

    success = bool(result.get("success"))

    if success:
        return ToolResult(
            tool_name=tool_name,
            success=True,
            data=result,
        )

    return ToolResult(
        tool_name=tool_name,
        success=False,
        error=result.get(
            "error",
            "Tool execution failed.",
        ),
        data=result,
    )


def run_tools(
    session: Session,
    user_id: int,
    tool_calls: list[ToolCall],
) -> list[ToolResult]:
    """
    Execute multiple agent tool calls through the same
    verification/security gate.
    """

    results: list[ToolResult] = []

    for tool_call in tool_calls:
        results.append(
            run_tool(
                session=session,
                user_id=user_id,
                tool_call=tool_call,
            )
        )

    return results


def tool_result_to_text(
    tool_results: list[ToolResult],
) -> str:
    """
    Convert tool results into text that can be supplied
    back to the agent/final-answer generation step.
    """

    if not tool_results:
        return "No tool results were produced."

    sections: list[str] = []

    for index, result in enumerate(
        tool_results,
        start=1,
    ):
        sections.append(
            f"Tool Result {index}\n"
            f"Tool: {result.tool_name}\n"
            f"Success: {result.success}\n"
            f"Data: {result.data}\n"
            f"Error: {result.error}"
        )

    return "\n\n".join(sections)