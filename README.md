# Deep Research

ローカル環境で LangGraph + Ollama によるリサーチ型AIエージェントを構築するためのコードです。  

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
        ├── __init__.py
        ├── configuration.py
        ├── graph.py
        ├── prompts.py
        └── utils.py
```

---

## 📄 ライセンス

MIT License

Copyright (c) 2025 shanigoro48256

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---
