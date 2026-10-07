from typing import Any, Annotated, Sequence, TypedDict
import operator

from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END

from app.config import get_settings
from app.services.tools.registry import get_tool, get_tools

settings = get_settings()

class AgentState(TypedDict):
    message: str
    iterations: int
    tools_used: list[str]
    tool_calls: list[dict]
    sources: list[dict]
    final_response: str
    contents: list[Any]
    current_function_calls: list[Any]
    next_step: str  # To decide conditional routing

class GraphAgentService:
    def __init__(self):
        self.settings = get_settings()
        self.client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        
        self.tools = []
        for tool in get_tools():
            self.tools.append(
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration.from_callable(callable=tool, client=self.client)
                    ]
                )
            )

        self.graph = self._build_graph()

    def _build_tool_config(self):
        return types.GenerateContentConfig(
            tools=self.tools,
            temperature=self.settings.AGENT_TEMPERATURE,
        )

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("understand_plan", self._node_understand_plan)
        workflow.add_node("tool_execution", self._node_tool_execution)
        workflow.add_node("observe", self._node_observe)
        workflow.add_node("generate_response", self._node_generate_response)
        
        workflow.set_entry_point("understand_plan")

        workflow.add_conditional_edges(
            "understand_plan",
            lambda x: x["next_step"],
            {
                "tool_execution": "tool_execution",
                "generate_response": "generate_response"
            }
        )

        workflow.add_edge("tool_execution", "observe")
        workflow.add_edge("observe", "understand_plan")

        return workflow.compile()
        
    async def _node_understand_plan(self, state: AgentState) -> dict:
        iterations = state.get("iterations", 0) + 1
        contents = state.get("contents", [])
        
        if iterations > self.settings.AGENT_MAX_ITERATIONS:
            return {
                "iterations": iterations,
                "next_step": "generate_response"
            }
            
        response = await self.client.aio.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=contents,
            config=self._build_tool_config(),
        )

        function_calls = self._extract_function_calls(response)

        new_contents = list(contents)
        if response.candidates and response.candidates[0].content:
            new_contents.append(response.candidates[0].content)

        return {
            "iterations": iterations,
            "contents": new_contents,
            "current_function_calls": function_calls,
            "next_step": "tool_execution" if function_calls else "generate_response",
            "final_response": response.text if not function_calls else ""
        }

    async def _node_tool_execution(self, state: AgentState) -> dict:
        function_calls = state.get("current_function_calls", [])
        tool_calls = []
        tools_used = []
        sources = []
        function_response_parts = []

        for function_call in function_calls:
            tool_name = function_call.name
            arguments = dict(function_call.args) if function_call.args else {}

            tools_used.append(tool_name)

            execution = await self._execute_tool(tool_name, arguments)
            result = execution.get("result")

            self._extract_sources(tool_name, result, sources)

            tool_calls.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result if execution["success"] else execution.get("error"),
                "success": execution["success"],
            })

            function_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={
                        "result": result if execution["success"] else {"error": execution.get("error")}
                    },
                )
            )

        new_contents = list(state.get("contents", []))
        if function_response_parts:
            new_contents.append(
                types.Content(
                    role="user",
                    parts=function_response_parts,
                )
            )

        existing_tools_used = list(state.get("tools_used", []))
        existing_tools_used.extend([t for t in tools_used if t not in existing_tools_used])
        
        existing_tool_calls = list(state.get("tool_calls", []))
        existing_tool_calls.extend(tool_calls)
        
        existing_sources = list(state.get("sources", []))
        existing_sources.extend(sources)

        return {
            "contents": new_contents,
            "tools_used": existing_tools_used,
            "tool_calls": existing_tool_calls,
            "sources": existing_sources,
        }

    async def _node_observe(self, state: AgentState) -> dict:
        # In a more complex setup, this might evaluate if the tool result was helpful
        # and summarize it before passing back to the planner.
        # Here we just pass through since contents were updated in tool_execution.
        return {}
        
    async def _node_generate_response(self, state: AgentState) -> dict:
        final_response = state.get("final_response", "")
        
        if not final_response:
            if state.get("iterations", 0) > self.settings.AGENT_MAX_ITERATIONS:
                final_response = "I reached the maximum number of agent steps before completing the task. Please try narrowing the request."
            else:
                final_response = "I have completed the task."

        return {
            "final_response": final_response
        }

    async def _execute_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        tool = get_tool(name)
        if tool is None:
            return {"success": False, "error": f"Unknown tool: {name}"}
        try:
            result = tool(**arguments)
            return {"success": True, "result": result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _extract_function_calls(self, response) -> list:
        function_calls = []
        if not response.candidates:
            return function_calls
        candidate = response.candidates[0]
        if not candidate.content:
            return function_calls
        for part in candidate.content.parts:
            if part.function_call:
                function_calls.append(part.function_call)
        return function_calls

    def _extract_sources(self, tool_name: str, result: Any, sources: list):
        if tool_name != "search_knowledge_base":
            return
        if not isinstance(result, dict):
            return
        results = result.get("results", [])
        for item in results:
            sources.append({
                "document_id": item.get("document_id"),
                "chunk_index": item.get("chunk_index"),
                "score": item.get("similarity", 0),
            })

    async def run(self, message: str) -> dict:
        initial_state = {
            "message": message,
            "iterations": 0,
            "tools_used": [],
            "tool_calls": [],
            "sources": [],
            "final_response": "",
            "contents": [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message)],
                )
            ],
            "current_function_calls": [],
            "next_step": ""
        }

        final_state = await self.graph.ainvoke(initial_state)

        return {
            "response": final_state.get("final_response", ""),
            "iterations": final_state.get("iterations", 1),
            "tools_used": final_state.get("tools_used", []),
            "tool_calls": final_state.get("tool_calls", []),
            "sources": self._deduplicate_sources(final_state.get("sources", [])),
        }

    @staticmethod
    def _deduplicate_sources(sources: list) -> list:
        unique = {}
        for source in sources:
            key = (source.get("document_id"), source.get("chunk_index"))
            if key not in unique:
                unique[key] = source
        return list(unique.values())


agent_service = GraphAgentService()
