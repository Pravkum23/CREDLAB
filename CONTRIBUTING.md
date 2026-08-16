# Contributing

CREDLAB welcomes narrowly scoped improvements to data normalization, tests, documentation, and visual evidence. Open an issue before proposing a new analytical framework.

Every contribution must follow `AGENTS.md`: never invent data, preserve historical periods, expose missing values, document assumptions and heuristics, and test material calculations.

## Development checks

```bash
python -m pytest -q
python -m compileall -q credlab run_pipeline.py
node --check web/app.js
```

Do not commit raw SEC cache files or secrets. A data refresh must use a valid `SEC_USER_AGENT` identifying the application and a contact address.

