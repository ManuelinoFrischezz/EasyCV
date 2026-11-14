"""Graph nodes for the CV tailoring workflow.

Each function in this module is a node in the LangGraph graph.
Nodes take the current state and return updates to merge into it.
"""

from pathlib import Path
from typing import Any

import yaml
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from easycv.extraction import extract_pdf
from easycv.graph.state import AgentResponse, GraphState, JobAnalysis
from easycv.llm.cv_parser import parse_cv
from easycv.llm.factory import create_llm
from easycv.schemas import CVData
from easycv.settings import Settings

# Paths to config files
CONFIGS_DIR = Path(__file__).parents[3] / "configs"
LAYOUTS_PATH = CONFIGS_DIR / "layouts.yml"
JOB_ANALYZER_PROMPTS_PATH = CONFIGS_DIR / "prompts" / "job_analyzer.yml"
CV_AGENT_PROMPTS_PATH = CONFIGS_DIR / "prompts" / "cv_agent.yml"


def extract_node(state: GraphState, settings: Settings) -> dict[str, Any]:  # noqa: ARG001
    """Extract text and links from PDF.

    This node uses PyMuPDF to extract raw content from the PDF.
    No LLM is involved.

    Args:
        state: Current graph state.
        settings: Application settings (unused, but kept for consistent node signature).
    """
    extracted = extract_pdf(state["pdf_bytes"])

    return {
        "extracted": extracted,
    }


def parse_node(state: GraphState, settings: Settings) -> dict[str, Any]:
    """Parse extracted content into structured CV data.

    This node uses an LLM to transform raw text into CVData.
    The result is stored as both original_cv (immutable) and current_cv.
    """
    extracted = state["extracted"]
    if extracted is None:
        raise ValueError("Cannot parse: no extracted content in state")

    cv_data = parse_cv(extracted, settings)

    return {
        "original_cv": cv_data,
        "current_cv": cv_data,
        "stage": "chat",
    }


def analyze_job_node(state: GraphState, settings: Settings) -> dict[str, Any]:
    """Analyze the job description and compare to CV.

    This node extracts structured information from the job posting
    and identifies gaps compared to the candidate's CV.
    """
    job_description = state["job_description"]
    current_cv = state["current_cv"]

    if current_cv is None:
        raise ValueError("Cannot analyze job: no CV data in state")

    llm = create_llm(settings)
    structured_llm = llm.with_structured_output(JobAnalysis)

    prompts = _load_prompts(JOB_ANALYZER_PROMPTS_PATH)
    cv_summary = _create_cv_summary(current_cv)

    system_prompt = prompts["system"]
    user_prompt = prompts["user"].format(
        job_description=job_description,
        cv_summary=cv_summary,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    job_analysis = structured_llm.invoke(messages)

    # Create initial message to user summarizing the analysis
    initial_message = _create_initial_message(job_analysis)  # type: ignore[arg-type]

    return {
        "job_analysis": job_analysis,
        "messages": [AIMessage(content=initial_message)],
    }


def agent_node(state: GraphState, settings: Settings) -> dict[str, Any]:
    """Process user message and optionally update the CV.

    This is the main conversational node. It takes the user's request,
    decides whether to modify the CV, and responds.

    Currently implements a simple LLM call. In the future, this will
    be upgraded to an agent with tools for layout modifications.
    """
    original_cv = state["original_cv"]
    current_cv = state["current_cv"]
    job_analysis = state["job_analysis"]
    messages = state["messages"]

    if original_cv is None or current_cv is None or job_analysis is None:
        raise ValueError("Cannot run agent: missing CV or job analysis in state")

    # Get the last user message
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        raise ValueError("Expected last message to be from user")

    user_message = last_message.content

    # Check for exit commands
    if _is_exit_command(str(user_message)):
        return {
            "stage": "done",
            "messages": [AIMessage(content="Your CV is ready! Good luck with your application.")],
        }

    llm = create_llm(settings)
    structured_llm = llm.with_structured_output(AgentResponse)

    prompts = _load_prompts(CV_AGENT_PROMPTS_PATH)
    layout_descriptions = _load_layout_descriptions()

    system_prompt = prompts["system"].format(
        original_cv=original_cv.model_dump_json(indent=2),
        current_cv=current_cv.model_dump_json(indent=2),
        job_analysis=job_analysis.model_dump_json(indent=2),
        layout_descriptions=layout_descriptions,
    )
    user_prompt = prompts["user"].format(user_message=user_message)

    # Build conversation context (system + history + current)
    llm_messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

    # Add relevant conversation history (skip the system-generated initial message)
    for msg in messages[1:-1]:  # Exclude first AI message and last user message
        llm_messages.append(msg)

    llm_messages.append(HumanMessage(content=user_prompt))

    response: AgentResponse = structured_llm.invoke(llm_messages)  # type: ignore[assignment]

    result: dict[str, Any] = {
        "messages": [AIMessage(content=response.message)],
    }

    if response.updated_cv is not None:
        result["current_cv"] = response.updated_cv

    return result


def should_continue(state: GraphState) -> str:
    """Determine the next step based on current state.

    Returns:
        "agent" to continue the conversation
        "end" to finish the workflow
    """
    if state["stage"] == "done":
        return "end"
    return "agent"


# =============================================================================
# Helper functions
# =============================================================================


def _load_prompts(path: Path) -> dict[str, str]:
    """Load prompt templates from a YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Prompt config not found: {path}")

    with path.open() as f:
        prompts: dict[str, str] = yaml.safe_load(f)

    return prompts


def _load_layout_descriptions() -> str:
    """Load layout descriptions from the registry."""
    if not LAYOUTS_PATH.exists():
        raise FileNotFoundError(f"Layout config not found: {LAYOUTS_PATH}")

    with LAYOUTS_PATH.open() as f:
        registry = yaml.safe_load(f)

    lines = []
    for name, config in registry.get("layouts", {}).items():
        desc = config.get("description", "No description").strip()
        lines.append(f"### {name}\n{desc}")

    return "\n\n".join(lines)


def _create_cv_summary(cv: CVData) -> str:
    """Create a brief text summary of the CV for job analysis."""
    parts = [f"Name: {cv.header.full_name}"]

    for section in cv.sections:
        parts.append(f"\n{section.heading}:")
        content = section.content

        if content.layout == "entries":
            for entry in content.entries:
                parts.append(f"  - {entry.title} at {entry.organization}")
        elif content.layout == "labeled_list":
            for item in content.items:
                parts.append(f"  - {item.label}: {', '.join(item.values)}")
        elif content.layout == "flat_list":
            for flat_item in content.items:
                parts.append(f"  - {flat_item}")
        elif content.layout == "paragraph":
            # Truncate long paragraphs
            text = content.text[:200]
            if len(content.text) > 200:
                text += "..."
            parts.append(f"  {text}")

    return "\n".join(parts)


def _create_initial_message(job_analysis: JobAnalysis) -> str:
    """Create the initial message to the user after job analysis."""
    parts = [f"I've analyzed the job posting for **{job_analysis.title}**"]

    if job_analysis.company:
        parts[0] += f" at **{job_analysis.company}**"

    parts[0] += ".\n"

    if job_analysis.required_skills:
        parts.append(f"**Key skills required:** {', '.join(job_analysis.required_skills)}")

    if job_analysis.gaps:
        parts.append(f"\n**Potential gaps I noticed:** {', '.join(job_analysis.gaps)}")
        parts.append("\nWould you like me to help address any of these?")
    else:
        parts.append("\nYour CV looks well-aligned with this role!")

    parts.append("\n\nHow would you like me to tailor your CV?")

    return "\n".join(parts)


def _is_exit_command(message: str) -> bool:
    """Check if the user wants to finish the conversation."""
    exit_phrases = [
        "done",
        "finish",
        "exit",
        "quit",
        "that's all",
        "looks good",
        "perfect",
        "i'm done",
    ]
    message_lower = message.lower().strip()
    return any(phrase in message_lower for phrase in exit_phrases)
