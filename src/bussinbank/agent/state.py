# src/bussinbank/agent/state.py
"""
This is the backpack that travels through the entire conversation.
Every single thing that happens gets stored here.
"""

from __future__ import annotations

from typing import Annotated, Literal, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The only thing that moves between nodes.
    Think of it as a dict that gets passed around.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: Literal["agent", "tools", "__end__"]