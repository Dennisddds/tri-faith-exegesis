# Data directory

Runtime outputs are generated locally and are **not** committed to GitHub.

| Path | Contents |
|------|----------|
| `corpus/` | Full scripture units from `crawl-full` |
| `gt/` | Later commentaries used as ground truth |
| `gt_sources/` | Optional local commentary files you provide |
| `gt_structured/` | GT converted into the interpretation schema |
| `interpretations/` | Model chain-of-thought interpretations |
| `alignments/` | Prediction-vs-GT scores |
| `graphs/` | Knowledge-graph JSON / HTML / GraphML |
| `jobs/` | SQLite resume state for `batch` |
| `cache/` | Mirror caches (e.g. Qur’an CDN) |

Rebuild:

```bash
python main.py crawl-full --tradition all
python main.py crawl-gt --tradition all
python main.py batch --tradition all --limit 3
```
