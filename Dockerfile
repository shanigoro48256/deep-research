# ========= ベースイメージ =========
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# ========= システム依存パッケージ =========
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    nano \
    curl \
    pciutils \
    lshw \
    graphviz \
    libgraphviz-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ========= Ollama のインストール =========
RUN curl -fsSL https://ollama.com/install.sh | sh

# ========= 作業ディレクトリ設定 =========
WORKDIR /app

# ========= アプリケーションコードをコピー =========
COPY . /app

# ========= Python 仮想環境の構築 =========
RUN python3 -m venv /app/.venv

# ========= 仮想環境を.bashrcに追加 =========
RUN echo "source /app/.venv/bin/activate" >> /root/.bashrc

# ========= JupyterLab のインストール =========
RUN /app/.venv/bin/pip install --upgrade pip && \
    /app/.venv/bin/pip install jupyter jupyterlab

# ========= LangChain & 関連パッケージをバージョン指定でインストール =========
RUN /app/.venv/bin/pip install \
    langgraph>=0.2.55 \
    langchain-community>=0.3.9 \
    tavily-python>=0.5.0 \
    langchain-ollama>=0.2.1 \
    duckduckgo-search>=7.3.0 \
    langchain-openai>=0.1.1 \
    openai>=1.12.0 \
    langchain_openai>=0.3.9 \
    httpx>=0.28.1 \
    markdownify>=0.11.0

# ========= 起動時に bash を実行 =========
CMD ["/bin/bash"]
