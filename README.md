# PatchPilot AI — Find it. Fix it. Prove it.

**PatchPilot AI** is a local-first, open-source Python security review workbench. It combines AST-based heuristic scanning with a local open-weight model through Ollama, then provides explicit syntax/pytest verification and an exportable JSON report.

> **Status:** Hackathon MVP. This is an educational prototype, not a production-grade SAST tool or a guarantee that code is secure.

## Why PatchPilot?

AI-generated and hand-written code can contain risky patterns. PatchPilot aims to make a review loop tangible: identify a suspicious construct, show the exact evidence, ask a local model for a cautious explanation, then verify a candidate separately rather than silently rewriting files.

## Features

- AST-based checks for `eval()`/`exec()`, subprocess calls with `shell=True`, `pickle.load()`, potentially unsafe `yaml.load()`, and `assert` used for runtime checks.
- Conservative line-based heuristics for credential-like assignments and common token shapes. Suspected assigned secrets are redacted in evidence.
- Local-only model call to Ollama; no proprietary AI API is used.
- Manual candidate-patch area; PatchPilot never applies an AI patch automatically.
- Python syntax check and an optional minimal pytest smoke check in a temporary directory.
- JSON report export and a dark, responsive Streamlit dashboard.

## Architecture

```text
Python source
   ↓
AST + heuristic scanner (patchpilot/scanner.py)
   ↓
Findings with rule IDs, severity, line and evidence
   ↓ (only when you click Explain)
Local Ollama model (patchpilot/ai_engine.py)
   ↓
Human-reviewed remediation advice
   ↓ (only when you explicitly request verification)
Syntax check / minimal pytest smoke check (patchpilot/verifier.py)
   ↓
JSON report
```

## Requirements

- macOS 14+ recommended for the current Ollama macOS app
- Python 3.10+
- Git
- Ollama
- A small local model; default: `qwen2.5:1.5b`
- 8 GB RAM can be tight depending on other apps and model context; close memory-heavy apps if needed.

## Run on macOS

Open Terminal in this project directory.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install Ollama from <https://ollama.com/download>, then pull the model:

```bash
ollama pull qwen2.5:1.5b
```

If Ollama is not already running, open the Ollama app. In another terminal you can start its service with:

```bash
ollama serve
```

If Ollama says the port is already in use, the service is already running; do not start a second copy. Check the installed model with:

```bash
ollama list
```

Run scanner tests:

```bash
python -m pytest -q
```

Start the dashboard:

```bash
streamlit run app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`. Open it in your browser.

## First demo

1. Leave the sample code in the editor or click **Load demo sample**.
2. Click **Run AST Security Scan**.
3. Expand a finding and point out the rule ID, exact line, and recommendation.
4. Click **Explain findings with local AI** to ask your local Ollama model for a grounded review.
5. Manually review a suggested fix and paste the candidate into the verification area.
6. Click **Check Python syntax**. The optional pytest button is gated by an explicit confirmation checkbox.
7. Export the JSON report.

## Safety and limitations

- **Heuristic scanner:** may produce false positives and false negatives. It does not perform full data-flow analysis, dependency analysis, or exploitability validation.
- **Model output:** is advisory, can be wrong, and is not a verified patch. Review every recommendation.
- **Local privacy:** code is sent to the local Ollama endpoint only after you explicitly click the AI explanation button. Do not paste production secrets into a demo.
- **Verification:** the MVP syntax check does not execute the candidate. The optional pytest smoke tests only check that a temporary file exists and is non-empty; they do not prove a fix is secure. A temporary directory is not a security sandbox. Only run tests on code you trust.
- **YAML:** the scanner reports `yaml.load()` unless it can see a `yaml.SafeLoader` loader. Review results against the installed PyYAML version.
- **Secrets:** the secret scanner is intentionally conservative and may miss credentials. Rotate real exposed credentials; removing them from a working file alone may not remove them from Git history.

## Open-weight model and license

PatchPilot does not bundle model weights and does not call a proprietary AI API. It invokes a model installed locally in Ollama. The default model tag is `qwen2.5:1.5b`; review the model card and license from the model publisher before redistributing weights or using the model in a commercial product. The application code is licensed under MIT (see `LICENSE`); the model's terms are separate.

## Project layout

```text
patchpilot_ai/
├── app.py
├── patchpilot/
│   ├── __init__.py
│   ├── scanner.py
│   ├── ai_engine.py
│   └── verifier.py
├── tests/
│   └── test_scanner.py
├── sample_vulnerable.py
├── requirements.txt
├── README.md
├── DEVTO.md
├── LICENSE
└── .gitignore
```

## Contributing

Issues and pull requests are welcome. Good first contributions: add tests for new rules, document false positives, improve rule explanations, and add safe fixtures. Never submit real credentials or exploit payloads targeting systems you do not own or have permission to test.

## License

MIT for the PatchPilot application code. See `LICENSE`. Third-party model licenses are separate.
