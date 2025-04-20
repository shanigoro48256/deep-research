from datetime import datetime

def get_current_date():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

query_writer_instructions = """あなたは目的に特化したウェブ検索クエリの作成者です。"""

query_writer_user="""
<GOAL>
WEB検索用のクエリを作成します。
</GOAL>

<REQUIREMENT>
1.{research_topic}に基づいてウェブ検索用のクエリを生成してください。
2.{current_date}の日付時点での最新情報を考慮してクエリを作成してください。
</REQUIREMENT>

<FORMAT>
以下の2つのキーを含むJSONオブジェクトとして返答してください（キー名は必ず下記の通り）:
   - "query": 実際の検索クエリ文字列
   - "rationale": このクエリがなぜ適切かを説明する短い理由
</FORMAT>

<EXAMPLE>
Example output:
{{
    "query": "トランスフォーマー アーキテクチャ 解説",
    "rationale": "トランスフォーマーモデルの基本構造を理解するため"
}}
</EXAMPLE>

回答はJSON形式で提供してください。:
"""

summarizer_instructions = """
あなたはWeb検索結果をもとに、高品質な日本語ドキュメントを作成するアシスタントです。
"""

summarizer_user = """
<GOAL>
Web検索結果に基づいて、ユーザーの関心トピックに関するドキュメントを作成してください。
</GOAL>

<REQUIREMENTS>
1. RESEARCH TOPICに関連する情報をRESEARCH RESULTから抽出して詳しく記述してください。
2. RESEARCH TOPICに関連しない情報や価値のない冗長な文はRESEARCH RESULTから無視してください。
3. 実質的な内容を含まない文章（ナビゲーション、言語切り替え、リンク誘導、メニュー情報など）は省いてください。
   ###RESEARCH TOPIC:{research_topic}
   ###RESEARCH RESULT:{most_recent_web_research}
4. EXISTING SUMMARYが空でない場合は、EXISTING SUMMARYを残しつつ、RESEARCH RESULTから抽出した情報を追加してください。
   ###EXISTING SUMMARY:{existing_summary}
5. EXISTING SUMMARYが空である場合は、RESEARCH RESULTから抽出した情報を追加してください。
6. カテゴリごとに詳細な文章を作成してください。
</REQUIREMENTS>

<EXAMPLE>
###アーキテクチャー
###スペック
###ベンチマーク
###ソフトウェア
###ネットワーク
###設置環境
###コスト
###保守
</EXAMPLE>

<FORMATTING>
- タイトルや説明は不要です。本文から始めてください。
- XMLタグは使わないでください。
</FORMATTING>
"""

reflection_instructions = """あなたはトピックに関する要約を分析する専門的なリサーチアシスタントです。"""

reflection_user = """
<GOAL>
ドキュメントの不足分を埋める検索クエリ用の質問文を作成する
</GOAL>

<REQUIREMENTS>
1. RESEARCH TOPICに対するDOCUMENTの不足分を特定してください。
   ###RESEARCH TOPIC:{research_topic}
   ###DOCUMENT:{running_summary}
2. DOCUMENTの不足分を埋めるための具体的な質問文を1つ考えてください。
3. その質問文がPAST QUERYと異なる内容にしてください。
   ###PAST QUERY:{query_history}
4. 質問文は一文で短くシンプルにしてください。
</REQUIREMENTS>

<FORMAT>
以下のキーを含むJSON形式で出力してください:
- knowledge_gap: 足りない、または深掘りが必要な内容の説明
- follow_up_query: それを調べるための具体的な検索クエリ
</FORMAT>

<EXAMPLE>
Example output:
{{
    "knowledge_gap": "要約にはパフォーマンス評価指標やベンチマークに関する情報が不足している",
    "follow_up_query": "特定の製品のベンチマークの事例は？"
}}
</EXAMPLE>

分析結果はJSON形式で提供してください。:"""


requery_instructions = """あなたは短い検索クエリを生成する専門家です。"""

requery_user= """
<GOAL>
長文の質問を、WEB検索に適した掛け合わせのキーワードに変換します。
</GOAL>

<REQUIREMENTS>
LONG QUERYを、WEB検索に適した掛け合わせのキーワードに変換してください。
###LONG QUERY>:{long_query}
</REQUIREMENTS>

<FORMAT>
1. 出力は必ず JSON 形式で、キー "query" を含めてください。
2. 2キーワード程度の短いクエリをJSON形式で出力してください
</FORMAT>

<EXAMPLE>
{{
  "query": "NVIDIA B200 価格"
}}
</EXAMPLE>
"""

final_instructions ="""あなたは詳細で分かりやすいレポートを作成する日本語のアシスタントです。"""

final_user = """
<GOAL>
以下のDOCUMENTを、RESEARCH TOPICに沿って読みやすい文章になるように編集してください。
###DOCUMENT{running_summary}
###RESEARCH TOPIC{research_topic}
</GOAL>

<FORMAT>
1. 段落は、トピック、要約、詳細、情報源に分けてください。(トピックの見出しや、情報源の見出しは重複しない)
2. 要約は、詳細をまとめた内容にしてください。
3. 詳細は、カテゴリに分けて文章を作成してください。（カテゴリ1、カテゴリ2という単語は出力しない）
4. 情報源は、文末に記載してください。
</FORMAT>

<EXAMPLE>
##トピック:{research_topic}
##要約
##詳細
##情報源:{all_sources}
</EXAMPLE>

<FORMATTING>
- XMLタグは使わないでください。
</FORMATTING>
"""