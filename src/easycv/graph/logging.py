"""Logging utilities for agent debugging.

Logs agent requests and responses to JSON files for debugging purposes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

LOGS_DIR = Path(__file__).parents[3] / "logs" / "agent"


def log_agent_call(
    *,
    user_message: str,
    system_prompt: str,
    cv_summary: str,
    raw_response: Any = None,
    parsed_response: dict[str, Any] | None = None,
    error: str | None = None,
) -> Path:
    """Log an agent call for debugging.

    Args:
        user_message: The user's request to the agent.
        system_prompt: The full system prompt sent to the LLM.
        cv_summary: Summary of the current CV state.
        raw_response: Raw response from the LLM (before parsing).
        parsed_response: Parsed AgentResponse as dict.
        error: Error message if parsing/execution failed.

    Returns:
        Path to the created log file.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now()
    filename = timestamp.strftime("%Y-%m-%dT%H-%M-%S") + ".json"
    filepath = LOGS_DIR / filename

    log_entry = {
        "timestamp": timestamp.isoformat(),
        "input": {
            "user_message": user_message,
            "system_prompt": system_prompt,
            "cv_summary": cv_summary,
        },
        "output": {
            "raw_response": _safe_serialize(raw_response),
            "parsed_response": parsed_response,
            "error": error,
        },
    }

    filepath.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False))

    return filepath


def _safe_serialize(obj: Any) -> Any:
    """Safely serialize an object to JSON-compatible format."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(item) for item in obj]
    # For Pydantic models or other objects
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: _safe_serialize(v) for k, v in obj.__dict__.items()}
    return str(obj)
