from app.services.tools.calculator import calculate
from app.services.tools.datetime_tool import (
    get_current_time,
)
from app.services.tools.document_tool import (
    list_documents,
)
from app.services.tools.knowledge_tool import (
    search_knowledge_base,
)


TOOLS = [
    calculate,
    get_current_time,
    list_documents,
    search_knowledge_base,
]


TOOL_MAP = {
    tool.__name__: tool
    for tool in TOOLS
}


def get_tools():
    return TOOLS


def get_tool(
    name: str
):
    return TOOL_MAP.get(name)