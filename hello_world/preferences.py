from google.adk.tools import ToolContext


def session_preferences(action: str, tool_context: ToolContext, response_style: str = "") -> dict:
    """Get, set, or clear response style for this conversation only.

    Args:
        action: get to inspect, set to update, or clear to reset to standard.
        response_style: concise or standard when setting; omit otherwise.
    """
    if action not in ("get", "set", "clear"):
        return {"error": "Action must be get, set, or clear."}
    if action == "set":
        if response_style not in ("concise", "standard"):
            return {"error": "Response style must be concise or standard."}
        tool_context.state["response_style"] = response_style
    elif action == "clear":
        tool_context.state["response_style"] = "standard"
    return {"response_style": tool_context.state.get("response_style", "standard")}
