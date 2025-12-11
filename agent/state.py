# from typing import Annotated, List, Optional
# from typing_extensions import TypedDict
# from langgraph.graph.message import AnyMessage, add_messages

# class AgentState(TypedDict):
#     messages: Annotated[List[AnyMessage], add_messages]
#     patient_id: Optional[str]

from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages

# class AgentState(TypedDict):
#     messages: Annotated[List[AnyMessage], add_messages]
#     patient_id: Optional[str]
#     patient_name: Optional[str] # Crucial for "Thanks, Rose"
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    patient_id: Optional[str]
    patient_name: Optional[str]

    # New additions:
    new_patient: Optional[bool]          # user said "No" to "have you been here before?"
    pending_name: Optional[dict]         # {"first": "...", "last": "..."}
    pending_dob: Optional[bool]          # waiting for DOB before register_patient
