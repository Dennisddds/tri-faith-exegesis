# Tri-Faith-Exegesis

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Claude%20%7C%20Gemini-purple.svg)](.env.example)
[![GitHub stars](https://img.shields.io/github/stars/Dennisddds/tri-faith-exegesis?style=social)](https://github.com/Dennisddds/tri-faith-exegesis/stargazers)

**LLM chain-of-thought exegesis for Buddhism, Christianity, and Islam — with later commentaries as ground truth (GT), alignment scoring, and knowledge-graph export.**

> Primary scripture → CoT interpretation → commentary GT → lexical + LLM-judge alignment → interactive KG

If this project is useful, please ⭐ **star the repo** — it helps others discover comparative-religion NLP research tools.

---

## Why this project?

Most LLM “scripture Q&A” demos generate free-form answers without a measurable baseline.  
**Tri-Faith-Exegesis** treats classical commentaries (tafsir / biblical commentary / Atthakatha-style notes) as **ground truth**, then scores model readings against them.

Useful for:

- Comparative religion & digital humanities
- Faithful LLM evaluation (hallucination vs. tradition)
- Knowledge-graph construction over sacred corpora
- Multi-provider LLM experiments (OpenAI / Anthropic / Google)

---

## Pipeline

```text
Full corpus crawl
    → LLM chain-of-thought interpretation
    → Structure commentary GT into the same schema
    → Align prediction vs GT (F1 + LLM judge)
    → Export knowledge graphs (JSON / GraphML / HTML)
```

| Tradition | Primary text unit | Default GT |
|-----------|-------------------|------------|
| Islam | Qur’an ayah | Ibn Kathir tafsir |
| Christianity | Bible chapter (WEB) | Matthew Henry (mirror / local) |
| Buddhism | Early Nikaya sutta | Commentarial anchors + SuttaCentral blurb / local GT |

**Providers:** set `LLM_PROVIDER=openai|anthropic|gemini` in `.env`.

---

## Quick start

```bash
git clone https://github.com/Dennisddds/tri-faith-exegesis.git
cd tri-faith-exegesis

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
```

Fill in API keys for the provider you use. **Never commit `.env`.**

### Small debug run

```bash
python main.py crawl-full --tradition islam --max-surah 1
python main.py crawl-gt --tradition islam --max-units 7
python main.py batch --tradition islam --limit 1
python main.py status
python main.py align-summary
```

### Full corpus (slow, API cost)

```bash
python main.py crawl-full --tradition all
python main.py crawl-gt --tradition all
python main.py batch --tradition all
```

### UI

```bash
streamlit run app.py
```

---

## Configuration

See [`.env.example`](.env.example):

| Variable | Purpose |
|----------|---------|
| `LLM_PROVIDER` | `openai` / `anthropic` / `gemini` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | ChatGPT |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Claude |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini |

---

## Repository layout

```text
main.py                 CLI entrypoint
app.py                  Streamlit UI
config.py               Settings from environment
requirements.txt
.env.example            Key template (no real secrets)
src/
  crawlers/             Full scripture + GT crawlers
  corpus/               Unit schema & inventory
  llm/                  Multi-provider client + CoT prompts
  alignment/            GT structuring & evaluation
  knowledge_graph/      Graph build + visualization
  jobs/                 Resume-able batch runner (SQLite)
data/                   Runtime outputs (gitignored; see data/README.md)
```

---

## Alignment metrics

- **Lexical concept F1** — overlap of concepts/entities between model and GT schema
- **LLM judge scores** — coverage, doctrinal fidelity, hallucination penalty (0–1)
- **Missing / extra vs GT** — what the model omitted or invented relative to commentary

Batch jobs resume from `data/jobs/*.sqlite3`.

---

## Security

- This repository ships **no API keys**.
- Copy `.env.example` → `.env` and only fill the provider you use.
- Rotate any key that was ever pasted into chat or logs.

---

## Academic note

This is a research prototype. “Primary text” means publicly available early/authoritative layers (Arabic Uthmani Qur’an, Pali Nikayas, verse-anchored WEB Bible). GT commentaries are **selected traditions**, not exclusive truth. Estimate API cost before full-corpus runs.

---

## Contributing & visibility

Issues, PRs, and dataset/GT contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

**Topics:** `comparative-religion` · `llm` · `chain-of-thought` · `knowledge-graph` · `quran` · `bible` · `tipitaka` · `exegesis` · `nlp` · `digital-humanities`

---

## Author / Contact

- GitHub: [Dennisddds](https://github.com/Dennisddds)
- Email: [dengsiyang@hust.edu.cn](mailto:dengsiyang@hust.edu.cn)

## Citation

```bibtex
@software{tri_faith_exegesis,
  title  = {Tri-Faith-Exegesis: LLM Chain-of-Thought Scripture Interpretation with Commentary GT Alignment},
  author = {Dennisddds},
  email  = {dengsiyang@hust.edu.cn},
  year   = {2026},
  url    = {https://github.com/Dennisddds/tri-faith-exegesis}
}
```

## License

[Apache-2.0](LICENSE)
