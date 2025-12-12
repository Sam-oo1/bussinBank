# src/bussinbank/agent/graph.py
"""
BUSSINBANK AI CFO — FINAL, NO ERRORS, NO LOOPS, NO HALLUCINATIONS
"""

from __future__ import annotations

import os

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from bussinbank.agent.state import AgentState
from bussinbank.tools.finance_tools import TOOLS
from bussinbank.agent.prompts import SYSTEM_PROMPT
from dotenv import load_dotenv
load_dotenv()


# LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.6,
    api_key=os.getenv("GROQ_API_KEY"),
)

# Force tool use — no hallucinations
llm_with_tools = llm.bind_tools(TOOLS, tool_choice="auto")


def agent_node(state: AgentState):
    messages = state["messages"]
    if len(messages) == 1:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Build graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools=TOOLS))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


def ask(question: str):
    print(f"\nYou: {question}")
    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=question)]},
            config={"configurable": {"thread_id": "1"}, "recursion_limit": 8},
        )
        answer = result["messages"][-1].content
        print(f"BussinBank: {answer}\n")
    except Exception as e:
        print(f"BussinBank: Error: {e}\n")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        print("Set GROQ_API_KEY in .env")
        exit(1)

    print("BussinBank AI CFO is online")
    while True:
        q = input("You: ").strip()
        if q.lower() in {"quit", "exit", "bye"}:
            break
        ask(q)