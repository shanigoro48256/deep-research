import json
from typing_extensions import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph
from deep_research.configuration import Configuration, SearchAPI
from deep_research.utils import deduplicate_and_format_sources, tavily_search, format_sources, perplexity_search, duckduckgo_search, strip_thinking_tokens, get_config_value
from deep_research.state import SummaryState, SummaryStateInput, SummaryStateOutput
from deep_research.prompts import query_writer_instructions,query_writer_user, summarizer_instructions,summarizer_user,reflection_instructions,reflection_user,get_current_date,requery_instructions,requery_user,final_instructions,final_user
from langsmith import traceable
from datetime import datetime

@traceable(name="generate_query_node")
def generate_query(state: SummaryState, config: RunnableConfig):
    """リサーチトピックに基づいて初期の検索クエリを生成します"""
    
    #設定情報（LLMや検索APIの情報）を取り出し
    configurable = Configuration.from_runnable_config(config)
    
    #LLMの設定
    llm_json_mode = ChatOllama(
        base_url=configurable.ollama_base_url, 
        model=configurable.local_llm,
        temperature=0, 
        format="json"
    )

    current_date = get_current_date()
    
    #プロンプトを与えてLLMを実行
    result = llm_json_mode.invoke(
        [SystemMessage(content=query_writer_instructions),
        HumanMessage(content=query_writer_user.format(
            current_date=current_date,
            research_topic=state.research_topic
        ))]
    )
    
    #LLMが生成した文字列を取得
    content = result.content

    #LLMの出力がJSON形式なら辞書に変換し、検索クエリを取得
    try:
        query = json.loads(content)
        search_query = query['query']
    #LLMの出力がJSONではない or "query" キーが存在しなかったら、
    except (json.JSONDecodeError, KeyError):
        #モデルの出力に含まれがちな余計なタグを除去
        if configurable.strip_thinking_tokens:
            content = strip_thinking_tokens(content)
        #テキストそのものをクエリとして使う
        search_query = content
    return {"search_query": search_query}

@traceable(name="web_research_node")
def web_research(state: SummaryState, config: RunnableConfig):
    """生成された検索クエリを使用してWeb検索を実行します。"""

    # 設定情報（LLMや検索APIの情報）を取り出し
    configurable = Configuration.from_runnable_config(config)

    #configurable.search_apiの設定値を文字列に変換する
    search_api = get_config_value(configurable.search_api)

    #search_apiによって、検索ツールを選択して、検索を実行する
    if search_api == "tavily":
        search_results = tavily_search(state.search_query, fetch_full_page=configurable.fetch_full_page, max_results=2)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, fetch_full_page=configurable.fetch_full_page)
    elif search_api == "perplexity":
        search_results = perplexity_search(state.search_query, state.research_loop_count)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, fetch_full_page=configurable.fetch_full_page)
    elif search_api == "duckduckgo":
        search_results = duckduckgo_search(state.search_query, max_results=3, fetch_full_page=configurable.fetch_full_page)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, fetch_full_page=configurable.fetch_full_page)
    else:
        raise ValueError(f"Unsupported search API: {configurable.search_api}")

    #検索結果の履歴があればそれを引き継ぎ、なければ空リストを作成
    sources_gathered = list(state.sources_gathered) if state.sources_gathered else []
    sources_gathered.append(format_sources(search_results))

    return {
        "sources_gathered": sources_gathered,
        "research_loop_count": state.research_loop_count + 1,
        "web_research_results": [search_str],
    }

@traceable(name="summarize_sources_node")
def summarize_sources(state: SummaryState, config: RunnableConfig):
    """Web検索の結果を要約します。"""

    existing_summary = state.running_summary

    #過去に実行したWeb検索結果の中から最後の結果を取得
    most_recent_web_research = state.web_research_results[-1]

    # 設定情報（LLMや検索APIの情報）を取り出し
    configurable = Configuration.from_runnable_config(config)
    
    #LLMの設定
    sum_llm = ChatOllama(
        base_url=configurable.ollama_base_url, 
        model=configurable.sum_llm,
        max_tokens=configurable.max_tokens,
        temperature=0,
    )

    #LLMにプロンプトを与えて実行
    result = sum_llm.invoke(
        [SystemMessage(content=summarizer_instructions),
         HumanMessage(content=summarizer_user.format(
             research_topic=state.research_topic,
             most_recent_web_research=most_recent_web_research,
             existing_summary=existing_summary
             )
        )]
    )
    
    #LLMが生成した要約をrunning_summaryとして返す
    running_summary = result.content
    #if configurable.strip_thinking_tokens:
        #running_summary = strip_thinking_tokens(running_summary)
    
    return {"running_summary": running_summary}

@traceable(name="reflect_on_summary_node")
def reflect_on_summary(state: SummaryState, config: RunnableConfig):
    """追加リサーチの内容を生成します。"""

    #設定情報（LLMや検索APIの情報）を取り出し
    configurable = Configuration.from_runnable_config(config)
    
    #LLMの設定
    llm_json_mode = ChatOllama(
        base_url=configurable.ollama_base_url, 
        model=configurable.local_llm,
        temperature=0, 
        format="json"
    )

    #プロンプトをLLMに与えて実行
    result = llm_json_mode.invoke(
        [SystemMessage(content=reflection_instructions),
         HumanMessage(content=reflection_user.format(
             research_topic=state.research_topic,
             running_summary=state.running_summary,
             query_history = "\n".join(f"- {q}" for q in state.query_history)
             ))
        ])
    
    try:
        #LLMが返したJSONをPythonの辞書に変換
        reflection_content = json.loads(result.content)
        #follow_up_queryのkeyからvalueを取り出す
        query = reflection_content.get('follow_up_query')
        #valueが空 or Noneの場合"{state.research_topic}"の汎用クエリを使う
        if not query:
            query = f"{state.research_topic}について教えて下さい"
    #JSON形式でない、follow_up_queryキーがない、などのエラーが出たら、{state.research_topic}の汎用クエリを使う
    except (json.JSONDecodeError, KeyError, AttributeError):
        query = f"{state.research_topic}について教えて下さい"

    #既存のquery_historyが存在する場合それを使い、なければ空リストを使う
    query_history = getattr(state, "query_history", []) or []
    query_history.append(query)

    return {
        "search_query": query,
        "query_history": query_history
    }

@traceable(name="generate_requery_node")
def generate_requery(state: SummaryState, config: RunnableConfig):
    """reflect_on_summaryの結果を元に検索クエリを作成します。"""

    #設定情報（LLMや検索APIの情報）を取り出し
    configurable = Configuration.from_runnable_config(config)

    #LLMの設定
    llm_json_mode = ChatOllama(
        base_url=configurable.ollama_base_url,
        model=configurable.local_llm,
        temperature=0,
        format="json"
    )

    #プロンプトをLLMに与えて実行
    result = llm_json_mode.invoke([
        SystemMessage(content=requery_instructions),
        HumanMessage(content=requery_user.format(long_query=state.search_query))
     ])
    content = result.content

    try:
        #JSONを辞書に変換
        parsed = json.loads(content)
        #queryのvalueを取り出す
        short_query = parsed["query"]
    #JSON形式でない、keyがない場合、テキストそのものをクエリとして使う
    except (json.JSONDecodeError, KeyError):
        if configurable.strip_thinking_tokens:
            content = strip_thinking_tokens(content)
        short_query = content

    #履歴があればそれを使い、なければ空リストを使う
    short_query_history = list(state.short_query_history) if state.short_query_history else []
    short_query_history.append(short_query)

    return {"search_query": short_query,
           "short_query_history": short_query_history}

@traceable(name="route_research_node")
def route_research(state: SummaryState, config: RunnableConfig) -> Literal["generate_requery", "finalize_summary"]:
    """追加の検索か最終的なサマリーに移行するかを決定します。"""

    configurable = Configuration.from_runnable_config(config)
    #ループ回数が設定された最大数に達していなければ、Web検索（generate_requery）へ進み
    if state.research_loop_count <= configurable.max_web_research_loops:
        return "generate_requery"
    #ループ回数が設定された最大数に達していれば、最終的な回答（finalize_summary）へ進む
    else:
        return "finalize_summary"


@traceable(name="finalize_summary_node")
def finalize_summary(state: SummaryState, config: RunnableConfig):
    """最終的なサマリーを作成します"""

    seen_urls = set()
    unique_source_lines = []

    #sources_gatheredに含まれる各ソースを改行で分割、空行や前後の空白を除外
    for source in state.sources_gathered:
        for line in source.split('\n'):
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("* "):
                #Markdownの*を取り除く
                content_after_asterisk = line_str[2:]
                #:で分割してタイトルとURLに分ける
                parts = content_after_asterisk.split(" : ", 1)
                #"タイトル:URL"の構造を持っているか確認
                if len(parts) == 2:
                    url = parts[1].strip()
                    #URLの重複を除外
                    if url not in seen_urls:
                        seen_urls.add(url)#URL
                        unique_source_lines.append(line_str)#"タイトル:URL"
                else:
                    #万が一パースできなかった場合は、行全体の重複を排除
                    if line_str not in seen_urls:
                        seen_urls.add(line_str)
                        unique_source_lines.append(line_str)
            else:
                #他のフォーマットの場合
                # ここでは行全体の重複を排除
                if line_str not in seen_urls:
                    seen_urls.add(line_str)
                    unique_source_lines.append(line_str)

    #情報源をまとめて改行で表示
    all_sources = "\n".join(unique_source_lines)

    #設定情報（LLMや検索APIの情報）を取り出し
    configurable = Configuration.from_runnable_config(config)

    #LLMの設定
    final_llm = ChatOllama(
        base_url=configurable.ollama_base_url,
        model=configurable.final_llm,
        max_tokens=configurable.max_tokens,
        temperature=0
    )
    
    #プロンプトをLLMに与えて実行
    result = final_llm.invoke([
        SystemMessage(content=final_instructions.format(
            research_topic=state.research_topic
            )
        ),
        HumanMessage(content=final_user.format(
            research_topic=state.research_topic,
            running_summary=state.running_summary,
            all_sources=all_sources
        ))
    ])

    final_report = result.content

    #結果をstateに反映
    state.running_summary = final_report
    return {"running_summary": final_report}

    
#ステートグラフの初期化
builder = StateGraph(SummaryState, input=SummaryStateInput, output=SummaryStateOutput, config_schema=Configuration)

#グラフにノードを追加
builder.add_node("generate_query", generate_query)#"ノード名",関数
builder.add_node("generate_requery", generate_requery)
builder.add_node("web_research", web_research)
builder.add_node("summarize_sources", summarize_sources)
builder.add_node("reflect_on_summary", reflect_on_summary)
builder.add_node("finalize_summary", finalize_summary)

#グラフにエッジを追加
builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "web_research")
builder.add_edge("generate_requery", "web_research")
builder.add_edge("web_research", "summarize_sources")
builder.add_edge("summarize_sources", "reflect_on_summary")
builder.add_conditional_edges("reflect_on_summary", route_research)#ループ回数により、generate_requery or finalize_summaryに遷移
builder.add_edge("finalize_summary", END)

#グラフのコンパイル
graph = builder.compile()