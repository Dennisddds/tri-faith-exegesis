# Contributing

Thanks for helping improve **Tri-Faith Exegesis**.

## Ways to contribute

- Report bugs or suggest features via [GitHub Issues](https://github.com/Dennisddds/tri-faith-exegesis/issues)
- Improve crawlers, alignment metrics, or prompts
- Add local ground-truth commentaries under `data/gt_sources/{tradition}/`
- Fix docs, typography, or UI copy
- Share reproducible small-scale eval results

## Development setup

```bash
git clone https://github.com/Dennisddds/tri-faith-exegesis.git
cd tri-faith-exegesis
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Use a small `--limit` / `--max-surah` when testing to avoid high API cost.

## Pull requests

1. Fork and create a feature branch
2. Keep changes focused and documented
3. Do not commit `.env`, API keys, or large `data/` run outputs
4. Open a PR against `main` with a short summary and test notes

## Code of conduct (short)

Be respectful of religious traditions and of other contributors. This project aims at scholarly comparison, not polemic.

## Contact

Maintainer: [dengsiyang@hust.edu.cn](mailto:dengsiyang@hust.edu.cn)
