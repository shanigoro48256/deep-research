import os
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal

from langchain_core.runnables import RunnableConfig

class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"

class Configuration(BaseModel):
    """ループ回数やLLM、検索APIの設定"""

    max_web_research_loops: int = Field(
        default=3,
        title="Research Depth",
        description="Number of research iterations to perform"
    )
    #JSON用LLM
    local_llm: str = Field(
        default="hhao/qwen2.5-coder-tools:32b",
        title="LLM Model Name",
        description="Name of the LLM model to use"
    )
    #思考用LLM
    sum_llm: str = Field(
        default="deepseek-ca",
        title="LLM Model Name",
        description="Name of the LLM model to use"
    )
    #日本語用LLM
    final_llm: str = Field(
        default="swallow31",
        title="LLM Model Name",
        description="Name of the LLM model to use"
    )
    max_tokens: int = Field(
        default=4096,
        title="Max Tokens",
        description="Maximum number of tokens to generate from LLM"
    )
    llm_provider: Literal["ollama"] = Field(
        default="ollama",
        title="LLM Provider",
        description="Provider for the LLM (Ollama)"
    )
    search_api: Literal["perplexity", "tavily", "duckduckgo"] = Field(
        default="duckduckgo",
        title="Search API",
        description="Web search API to use"
    )
    #ページの全文（HTMLなど）を取得するかどうか
    fetch_full_page: bool = Field(
        default=True,
        title="Fetch Full Page",
        description="Include the full page content in the search results"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434/",
        title="Ollama Base URL",
        description="Base URL for Ollama API"
    )
    #LLMの出力に含まれる <think> のような特殊トークンを削除するかどうか
    strip_thinking_tokens: bool = Field(
        default=True,
        title="Strip Thinking Tokens",
        description="Whether to strip <think> tokens from model responses"
    )
    
    #ノードに渡されたconfigが存在し、その中に"configurable"キーがあれば、それを取り出す（ないときは空の辞書）
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """RunnableConfigからConfigurationインスタンスを生成"""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        
        #Configurationに定義されたすべてのフィールド（model_fields）に対して、まず環境変数（name.upper）を優先的に使い、なければconfigurableの値を使う
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }
        
        #取得できた値からvalueのNoneを除外して、次のようなものを作っている。
        #例：Configuration(search_api="duckduckgo",max_web_research_loops=3,ollama_base_url="http://localhost:11434/")
        values = {k: v for k, v in raw_values.items() if v is not None}
        
        return cls(**values)