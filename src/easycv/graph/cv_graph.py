"""CV tailoring graph composition.

This module assembles the LangGraph graph that orchestrates the CV
tailoring workflow. The graph handles:
1. PDF extraction
2. CV parsing
3. Job description analysis
4. Conversational CV tailoring

Usage:
    >>> from easycv.graph import create_cv_graph
    >>> from easycv.settings import get_settings
    >>>
    >>> graph = create_cv_graph(get_settings())
    >>>
    >>> # Initial invocation with PDF and job description
    >>> result = graph.invoke({
    ...     "pdf_bytes": pdf_content,
    ...     "job_description": "We are looking for a Senior Data Scientist...",
    ...     "messages": [],
    ...     "stage": "init",
    ... })
    >>>
    >>> # Continue conversation
    >>> result = graph.invoke({
    ...     **result,
    ...     "messages": result["messages"] + [HumanMessage(content="Emphasize Python skills")],
    ... })
"""

from functools import partial

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from easycv.graph.nodes import (
    agent_node,
    analyze_job_node,
    extract_node,
    parse_node,
    render_node,
    should_continue,
)
from easycv.graph.state import GraphState
from easycv.settings import Settings


def create_cv_graph(
    settings: Settings, *, checkpointer: MemorySaver | None = None
) -> CompiledStateGraph[GraphState]:
    """Create the CV tailoring graph.

    Args:
        settings: Application settings for LLM configuration.
        checkpointer: Optional checkpointer for conversation persistence.
            If None, a MemorySaver is created (in-memory, for development).

    Returns:
        Compiled LangGraph graph ready for invocation.

    Example:
        >>> settings = get_settings()
        >>> graph = create_cv_graph(settings)
        >>>
        >>> # With persistence
        >>> from langgraph.checkpoint.memory import MemorySaver
        >>> checkpointer = MemorySaver()
        >>> graph = create_cv_graph(settings, checkpointer=checkpointer)
    """
    # Bind settings to node functions
    extract = partial(extract_node)
    parse = partial(parse_node, settings=settings)
    analyze_job = partial(analyze_job_node, settings=settings)
    agent = partial(agent_node, settings=settings)
    render = partial(render_node)

    # Build the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("extract", extract)
    workflow.add_node("parse", parse)
    workflow.add_node("analyze_job", analyze_job)
    workflow.add_node("agent", agent)
    workflow.add_node("render", render)

    # Define edges
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "parse")
    workflow.add_edge("parse", "analyze_job")
    workflow.add_edge("analyze_job", "agent")

    # Conditional edge: after agent, either render (if done) or end (wait for user)
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "end": END,  # Pause and wait for user input
            "render": "render",  # Generate final PDF
        },
    )

    # Render is the final node
    workflow.add_edge("render", END)

    # Compile with checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()

    return workflow.compile(checkpointer=checkpointer)


def create_initial_state(pdf_bytes: bytes, job_description: str) -> GraphState:
    """Create the initial state for a new CV tailoring session.

    Args:
        pdf_bytes: Raw PDF file content.
        job_description: Job description text.

    Returns:
        Initial GraphState ready for graph invocation.

    Example:
        >>> with open("resume.pdf", "rb") as f:
        ...     pdf_bytes = f.read()
        >>> state = create_initial_state(pdf_bytes, "Senior Data Scientist role...")
        >>> result = graph.invoke(state, config={"configurable": {"thread_id": "123"}})
    """
    return GraphState(
        pdf_bytes=pdf_bytes,
        job_description=job_description,
        extracted=None,
        original_cv=None,
        current_cv=None,
        job_analysis=None,
        messages=[],
        stage="init",
        rendered_pdf=None,
    )
