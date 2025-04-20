# Deep Research

ローカル環境で LangGraph + Ollama によるリサーチ型AIエージェントを構築するためのテンプレートです。  
本プロジェクトは **CUDA 12.1 / NVIDIA A100（80GB）** に対応し、Docker Compose 上で即実行可能です。

---

## 🔧 構成

- CUDA 12.1
- Python 3.10 + venv
- Ollama（ローカルLLMエンジン）
- Jupyter Lab（ブラウザUI）
- LangGraph / LangChain
- GPU NVIDIA A100 80GB

---

## 🚀 セットアップ手順

---

### Docker イメージをビルド & 起動

```bash
docker compose up --build
```
> ✅ `docker-compose.yml` 
> ✅ `DockerFile` 

### Jupyter Notebook にアクセス

ブラウザで次のURLを開いてください：

```
http://localhost:8888
```

トークン不要で Jupyter Lab が開きます。

---

### Notebook 上でリポジトリをクローン

Jupyter Lab のターミナルまたはノートブックのセル上で次を実行してください：

```bash
git clone https://github.com/shanigoro48256/deep-research.git
```

---

### Notebook を実行

クローンしたリポジトリ内の以下のファイルを開いて、実行してください

```
deep-research/main_demo.ipynb
```

## 📂 ディレクトリ構成（抜粋）

```
.
├── Dockerfile
├── docker-compose.yml
├── main_demo.ipynb
├── requirements.txt
└── src/
    └── deep_research/
        ├── configuration.py
        ├── graph.py
        ├── prompts.py
        └── utils.py
```

---

## 📄 ライセンス

MIT License

---
