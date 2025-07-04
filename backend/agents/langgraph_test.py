"""
注意: このファイルは旧バージョンのTavily検索を使用したテストファイルです。
現在はElasticsearchベースの検索に移行しているため、deep_research.pyを参照してください。
"""

from typing import Annotated

from langchain_google_genai import ChatGoogleGenerativeAI
from typing_extensions import TypedDict

# 注意: 以下のTavilyインポートは非推奨です
# from langchain_community.tools.tavily_search import TavilySearchResults
# from langchain_tavily import TavilySearch

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage

from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import get_model_instance, DEFAULT_CHAT_MODEL_ID

load_dotenv()

# 注意: Tavilyは非推奨、Elasticsearchベースのdeep_research.pyを使用してください

class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

# 各種ノードの定義
# LLM
llm = get_model_instance(DEFAULT_CHAT_MODEL_ID)
# ツール（注意: Tavilyは非推奨）
# tool = TavilySearch()
# tools = [tool]
tools = []  # 空のツールリスト
# LLMにツールを追加
llm_with_tools = llm.bind_tools(tools)



# 検索チャットノード（注意: 現在は検索機能が無効化されています）
def search_node(state: State):
    system_prompt = """
    注意: このテストファイルは旧バージョンです。Elasticsearch検索を使用する場合は、
    deep_research.pyのweb_searchまたはnews_search機能を使用してください。
    """
    messages_with_prompt = [{"role": "system", "content": system_prompt}] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages_with_prompt)]}

# 回答チャットノード
def answer_node(state: State):
    system_prompt = """
    注意: このテストファイルは旧バージョンです。
    現在はElasticsearchベースの検索に移行しています。
    deep_research.pyを使用してください。
    """
    messages_with_prompt = [{"role": "system", "content": system_prompt}] + state["messages"]
    return {"messages": [llm.invoke(messages_with_prompt)]}

tool_node = ToolNode(tools=tools)  # 空のツールリスト

# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("search_node", search_node)
graph_builder.add_node("tool_node", tool_node)
graph_builder.add_node("answer_node", answer_node)
graph_builder.set_entry_point("search_node")




def should_continue(state: State) -> str:
    """
    最後のメッセージにツールコールがあるかどうかを判断する。
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "continue"
    return "end"

# search_nodeの後に tool_node を挟み、再度回答生成へ
graph_builder.add_conditional_edges(
    "search_node",
    should_continue,
    {
        "continue": "tool_node",
        "end": "answer_node",
    },
)

# tool_nodeの後はanswer_nodeに戻る
graph_builder.add_edge("tool_node", "answer_node")

# 回答ノードの後はENDに戻る
graph_builder.add_edge("answer_node", END)

graph = graph_builder.compile()

def search_agent(question: str):
    return graph.invoke({"messages": [HumanMessage(content=question)]})

