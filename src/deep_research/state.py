import operator
from dataclasses import dataclass, field
from typing_extensions import Annotated
from typing import List

@dataclass(kw_only=True)
class SummaryState:
    research_topic: str = field(default=None) #リサーチトピック
    search_query: str = field(default=None) #検索クエリ
    web_research_results: Annotated[list, operator.add] = field(default_factory=list) #検索結果のテキスト一覧
    sources_gathered: List[str] = field(default_factory=list) #情報源（URLなど）の一覧
    research_loop_count: int = field(default=0) # Research loop count #Web検索のループ回数
    running_summary: str = field(default=None) #検索結果の要約
    query_history: List[str] = field(default_factory=list) #質問文の履歴
    short_query_history: List[str] = field(default_factory=list)#検索キーワードの履歴

#グラフに渡す最初の「入力値」
@dataclass(kw_only=True)
class SummaryStateInput:
    research_topic: str = field(default=None)

#グラフから返ってくる最終的な「出力値」
@dataclass(kw_only=True)
class SummaryStateOutput:
    running_summary: str = field(default=None)