# Tri-Faith-Exegesis

用大模型思维链阐释佛教、基督教、伊斯兰教**全量原典**，并 **以后人注疏为 Ground Truth（GT）** 做对齐评估与知识图谱导出。

支持 **ChatGPT（OpenAI） / Claude（Anthropic） / Gemini（Google）**，通过 `.env` 切换。

## 方法

```text
全量原典爬取 → LLM 思维链阐释 → 注疏 GT 结构化 → 对齐评估 → 知识图谱
```

| 传统 | 原典粒度 | 默认 GT |
|------|----------|---------|
| 伊斯兰教 | 逐节（ayah） | Ibn Kathir tafsir |
| 基督教 | 逐章（chapter） | Matthew Henry（镜像/本地） |
| 佛教 | 逐经（sutta，早期尼柯耶） | 注疏锚点 + SuttaCentral blurb / 本地 GT |

## 快速开始

```bash
git clone <your-repo-url>
cd Clarification

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
```

复制环境模板并填入密钥（**不要提交 `.env`**）：

```bash
cp .env.example .env
```

设置 `LLM_PROVIDER=openai|anthropic|gemini`，并填写对应 API Key。

### 调试小规模

```bash
python main.py crawl-full --tradition islam --max-surah 1
python main.py crawl-gt --tradition islam --max-units 7
python main.py batch --tradition islam --limit 1
python main.py status
python main.py align-summary
```

### 全量（耗时长、有 API 费用）

```bash
python main.py crawl-full --tradition all
python main.py crawl-gt --tradition all
python main.py batch --tradition all
```

### UI

```bash
streamlit run app.py
```

## 配置

见 [`.env.example`](.env.example)：

| 变量 | 说明 |
|------|------|
| `LLM_PROVIDER` | `openai` / `anthropic` / `gemini` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | ChatGPT |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Claude |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini |

## 仓库结构

```text
main.py                 CLI
app.py                  Streamlit UI
config.py               环境配置
requirements.txt
.env.example            密钥模板（无真实密钥）
src/
  crawlers/             全量原典与 GT 爬虫
  corpus/               单元 schema / inventory
  llm/                  多模型客户端（OpenAI/Claude/Gemini）与 CoT
  alignment/            GT 结构化与对齐评估
  knowledge_graph/      图谱构建与可视化
  jobs/                 断点续跑批处理
data/                   运行时产出（默认不入库，见 data/README.md）
```

## 安全

- 本仓库**不包含** API Key。
- 请使用 `.env.example` 复制为本地 `.env`，只填你实际使用的提供商密钥。

## 学术边界

本项目是研究原型：原典取可公开获取文本层；GT 是选定注疏传统，不是唯一真理。全量跑通前请评估 API 费用与时间。
