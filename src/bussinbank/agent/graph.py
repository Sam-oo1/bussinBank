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

llm_with_tools = llm.bind_tools(TOOLS)


def agent_node(state: AgentState):
    """
    The agent calls the LLM, potentially triggering tool use or a final answer.
    """
    messages = state["messages"]
    # Prepend the system prompt only at the beginning of a new thread
    # or if the LLM hasn't been given instructions yet.
    if messages and not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    # Note: We let the LLM decide if it needs a tool or the final answer.
    # The graph structure handles the routing based on tool calls.

    return {"messages": [response]}

# 1. Initialize the StateGraph
builder = StateGraph(AgentState)

# 2. Add Nodes
builder.add_node("agent", agent_node)
# ToolNode automatically executes the tools defined in the previous message
builder.add_node("tools", ToolNode(TOOLS)) 


# 3. Define Edges and Conditionals
builder.add_edge(START, "agent")

# If 'agent' outputs a tool call, go to 'tools'. If not, go to 'END' (implies final answer or plain text).
builder.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", END: END},
)

# ⭐️ CRITICAL FIX: After 'tools' execute, send the results back to the 'agent'
# so the LLM can see the results and formulate the FINAL ANSWER.
builder.add_edge("tools", "agent") 

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


def ask(question: str):
    print(f"\nYou: {question}")
    # Using a fixed thread_id for this example
    config = {"configurable": {"thread_id": "1"}, "recursion_limit": 5} 

    # The input to the graph must be a list of messages.
    result = graph.invoke({"messages": [HumanMessage(content=question)]}, config=config)
    
    # The last message in the list is the final output of the graph.
    # We check if it contains the FINAL ANSWER.
    final_message_content = result["messages"][-1].content
    
    if "FINAL ANSWER:" in final_message_content:
        answer = final_message_content.split("FINAL ANSWER:")[-1].strip()
        print(f"BussinBank: {answer}\n")
        return
    
    # Fallback for when the graph ends without the specific keyword
    print(f"BussinBank: {final_message_content.strip()}")
    print("(Note: LLM didn't use 'FINAL ANSWER:' keyword.)\n")


# src/bussinbank/agent/graph.py - CORRECTION

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        print("Set GROQ_API_KEY in .env")
        exit(1)

    print("BussinBank AI CFO online")
    
    # ❌ REMOVE THIS LINE: It causes the Groq 400 error because the messages list is empty.
    # config = {"configurable": {"thread_id": "1"}}
    # graph.invoke({"messages": []}, config=config) 

    while True:
        try:
            q = input("You: ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        
        if q.lower() in {"quit", "exit"}:
            break
        if not q:
            continue
            
        ask(q)