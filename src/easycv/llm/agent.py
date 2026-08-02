"""Agent manager - PLACEHOLDER, TO BE REWRITTEN.

This file is kept for reference only. It has multiple issues documented in
spec/PROJECT_CONTEXT.md and will be completely rewritten:

Known issues:
- `create_agent` does not exist in langchain.agents
- Checkpointer is created but never passed to the agent
- No thread_id is used for conversation tracking
- System prompt is json.dumps of YAML content
- model_name setter does not rebuild the agent
- BASE_DIR via parents[2] breaks when installed as package
- Provider prefix and model names are hardcoded
- Prompt file extension mismatch (.yml vs .yaml)

Target design:
- One structured LLM call per turn, not an agent loop
- AgentTurn(message, updated_cv | None) return type
- LangGraph for state management with checkpointer
- Settings-based model configuration via pydantic-settings
"""

# Original code preserved for reference - DO NOT USE
#
# import json
# from pathlib import Path
#
# import yaml
# from langchain.agents import create_agent  # Does not exist!
# from langgraph.checkpoint.memory import InMemorySaver
#
#
# class AgentManager:
#
#     BASE_DIR = Path(__file__).resolve().parents[2]
#
#     def __init__(self,
#         model_name: str,
#         agent_middleware = None,
#         agent_tools = None,
#         checkpointer = None
#     ):
#         self._model_name = model_name
#         self.agent = create_agent(
#         model="openrouter:" + model_name,
#         tools=agent_tools or [],
#         system_prompt=self._retrieve_prompt()
#         )
#         self.checkpointer = InMemorySaver()
#
#     @property
#     def model_name(self):
#         return self._model_name
#
#     @model_name.setter
#     def model_name(self, new_name: str):
#         self._model_name = new_name
#
#     def invoke_agent(self, request: str) -> str:
#         response = self.agent.invoke(
#             input={"messages": [{"role": "user", "content": request}]}
#         )
#         return response["messages"][-1].content
#
#     def _retrieve_prompt(self) -> str:
#         prompt_yaml = self.BASE_DIR / "src" / "processing" / "prompts" / "agent_prompt.yaml"
#         with open(prompt_yaml, "r", encoding="utf-8") as file:
#             prompt = yaml.safe_load(file)
#         return json.dumps(prompt)
