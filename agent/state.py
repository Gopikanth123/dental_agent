from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    patient_id: Optional[str]