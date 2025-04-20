import os
import httpx
import requests
from typing import Dict, Any, List, Union, Optional

from markdownify import markdownify
from langsmith import traceable
from tavily import TavilyClient
from duckduckgo_search import DDGS

def get_config_value(value: Any) -> str:
    """
    設定値（文字列またはEnum）を文字列に変換します。
    
    Args:
        value (Any): 処理対象の設定値。文字列またはEnum型の値。
    
    Returns:
        str: 値の文字列表現
    
    Examples:
        >>> get_config_value("tavily")
        'tavily'
        >>> get_config_value(SearchAPI.TAVILY)
        'tavily'
    """
    return value if isinstance(value, str) else value.value

def strip_thinking_tokens(text: str) -> str:
    """
    <think>〜</think> タグとその中身をテキストから削除します。
    
    <think> と </think> に囲まれた内容をすべて取り除く処理を繰り返し実行します。
    
    Args:
        text (str): 処理対象のテキスト
    
    Returns:
        str: <think>タグとその中身が除去されたテキスト
    """
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>") + len("</think>")
        text = text[:start] + text[end:]
    return text

def deduplicate_and_format_sources(
    search_response: Union[Dict[str, Any], List[Dict[str, Any]]], 
    max_tokens_per_source: int, 
    fetch_full_page: bool = False
) -> str:
    """
    検索APIからの検索結果を整形＆重複除去します。
    
    単一の検索結果または検索結果のリストを受け取り、
    URLをキーとして重複を除去し、構造化されたテキスト形式に整形します。
    
    Args:
        search_response (dict または list): 以下のいずれか
            - 'results'キーを含む辞書
            - 辞書のリスト（各辞書が検索結果を含む）
        max_tokens_per_source (int): 各ソースごとの最大トークン数（目安：1トークン ≒ 4文字）
        fetch_full_page (bool, optional): ページ全文を含めるかどうか（デフォルトは False）
    
    Returns:
        str: 整形済みで重複のないソース情報を含む文字列
    
    Raises:
        ValueError: 入力が 'results' キーを持つ辞書でも、検索結果リストでもない場合
    """

    if isinstance(search_response, dict):
        sources_list = search_response['results']
    elif isinstance(search_response, list):
        sources_list = []
        for response in search_response:
            if isinstance(response, dict) and 'results' in response:
                sources_list.extend(response['results'])
            else:
                sources_list.extend(response)
    else:
        raise ValueError("Input must be either a dict with 'results' or a list of search results")
    
    unique_sources = {}
    for source in sources_list:
        if source['url'] not in unique_sources:
            unique_sources[source['url']] = source
    
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source: {source['title']}\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"
        if fetch_full_page:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get('raw_content', '')
            if raw_content is None:
                raw_content = ''
                print(f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
                
    return formatted_text.strip()

def format_sources(search_results: Dict[str, Any]) -> str:
    """
    検索結果をタイトル＋URLの箇条書きリストに整形します。
    
    各検索結果のタイトルとURLを "* タイトル : URL" の形式でリスト化します。
    
    Args:
        search_results (dict): 'results' キーに検索結果のリストを含む辞書
    
    Returns:
        str: 整形された文字列（箇条書き形式のソースリスト）
    """
    return '\n'.join(
        f"* {source['title']} : {source['url']}"
        for source in search_results['results']
    )

def fetch_raw_content(url: str) -> Optional[str]:
    """
    指定したURLからHTMLコンテンツを取得し、Markdown形式に変換します。
    
    10秒のタイムアウトを設定し、遅いサイトや大容量ページでのフリーズを防ぎます。
    
    Args:
    url (str): コンテンツを取得する対象のURL
    
    Returns:
    Optional[str]: Markdown形式で整形されたコンテンツ（成功時）、取得や変換に失敗した場合は None
    """

    try:                
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return markdownify(response.text)
    except Exception as e:
        print(f"Warning: Failed to fetch full page content for {url}: {str(e)}")
        return None

@traceable
def duckduckgo_search(query: str, 
                      max_results: int = 3, 
                      fetch_full_page: bool = False,
                      region: str = 'jp-jp', 
                      safesearch: str = 'moderate') -> Dict[str, List[Dict[str, Any]]]:
    """
    DuckDuckGoを使ってウェブ検索を実行し、結果を整形して返します。
    
    DDGSライブラリを用いて検索を行い、結果をフォーマットされた辞書として返します。
    
    Args:
        query (str): 実行する検索クエリ
        max_results (int, optional): 取得する最大検索件数（デフォルトは3）
        fetch_full_page (bool, optional): 各URLからページ全文を取得するかどうか（デフォルトは False）
    
    Returns:
        dict: 以下を含む辞書
            - results (list): 各検索結果の辞書リスト。各辞書は以下の項目を持つ：
                - title (str): 検索結果のタイトル
                - url (str): 検索結果のURL
                - content (str): ページ内容の要約・スニペット
                - raw_content (str or None): ページ全文（`fetch_full_page=True`のとき）
    """
    try:
        with DDGS() as ddgs:
            results = []
            search_results = list(ddgs.text(query,
                                            max_results=max_results,
                                            region=region,
                                            safesearch=safesearch,
                                           ))
            
            for r in search_results:
                url = r.get('href')
                title = r.get('title')
                content = r.get('body')
                
                if not all([url, title, content]):
                    print(f"Warning: Incomplete result from DuckDuckGo: {r}")
                    continue

                raw_content = content
                if fetch_full_page:
                    raw_content = fetch_raw_content(url)
                
                result = {
                    "title": title,
                    "url": url,
                    "content": content,
                    "raw_content": raw_content
                }
                results.append(result)
            
            return {"results": results}
    except Exception as e:
        print(f"Error in DuckDuckGo search: {str(e)}")
        print(f"Full error details: {type(e).__name__}")
        return {"results": []}
    
@traceable
def tavily_search(query: str, fetch_full_page: bool = True, max_results: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """
    Tavily APIを使ってウェブ検索を実行し、結果を整形して返します。
    
    TavilyClient を用いて検索を行います。TavilyのAPIキーは環境変数で設定されている必要があります。
    
    Args:
        query (str): 実行する検索クエリ
        fetch_full_page (bool, optional): ページ全文を含めるかどうか（デフォルトは True）
        max_results (int, optional): 最大取得件数（デフォルトは3）
    
    Returns:
        dict: 以下を含む辞書
            - results (list): 検索結果の辞書リスト（title, url, content, raw_content）
    """
     
    tavily_client = TavilyClient()
    return tavily_client.search(query, 
                         max_results=max_results, 
                         include_raw_content=fetch_full_page)

@traceable
def perplexity_search(query: str, perplexity_search_loop_count: int = 0) -> Dict[str, Any]:
    """
    Perplexity APIを使用してウェブ検索を実行し、結果を整形して返します。
    
    Perplexityの 'sonar-pro' モデルを使用して検索を実行します。
    PERPLEXITY_API_KEY の環境変数が必要です。
    
    Args:
        query (str): 検索クエリ
        perplexity_search_loop_count (int, optional): ループカウント（ソース番号表示用）
    
    Returns:
        dict: 以下を含む辞書
            - results (list): 検索結果の辞書リスト：
                - title (str): 検索回数とソース番号を含むタイトル
                - url (str): 情報源のURL
                - content (str): 検索内容またはサマリ
                - raw_content (str or None): ページ全文（1件目のみ）
    
    Raises:
        HTTPError: APIリクエストに失敗した場合
    """

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "Search the web and provide factual information with sources."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    }
    
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=payload
    )
    response.raise_for_status() 
    
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    citations = data.get("citations", ["https://perplexity.ai"])
    
    results = [{
        "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source 1",
        "url": citations[0],
        "content": content,
        "raw_content": content
    }]
    
    for i, citation in enumerate(citations[1:], start=2):
        results.append({
            "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source {i}",
            "url": citation,
            "content": "See above for full content",
            "raw_content": None
        })
    
    return {"results": results}