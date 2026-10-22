# PatchPilot AI: Find it. Fix it. Prove it. — a local-first security workbench

**Tags:** `#hf26` `#opensource` `#python` `#ai`

## The idea

AI can help developers write code faster, but speed does not remove the need for security review. A risky function call can slip into a prototype long before anyone thinks to run a scanner.

For Hacktoberfest, I built **PatchPilot AI**, a small local-first Python security workbench designed around a simple loop: find a suspicious pattern, understand the evidence, review a remediation suggestion, and verify a candidate separately.

## What it does

PatchPilot uses Python's `ast` module to flag a handful of patterns, including dynamic `eval()`/`exec()`, subprocess calls with `shell=True`, potentially unsafe deserialization, and credential-like assignments. Every finding includes a rule ID, severity, line number, evidence, and a suggested direction for remediation.

When the user explicitly asks for an AI review, PatchPilot sends the source excerpt and scanner findings to a **locally running open-weight model through Ollama**. There is no proprietary cloud AI API in the project. The model provides a risk summary and remediation advice, but the human remains in control: the app does not silently apply patches.

The final step checks candidate Python syntax and offers an optional minimal pytest smoke check. The current pytest check is intentionally modest: it verifies the temporary candidate file exists and is non-empty. It does not prove that a security fix is correct, and the app warns users that temporary directories are not a sandbox.

## Stack

- Python and `ast` for static checks
- Ollama with a locally installed open-weight model
- Streamlit for the interactive dashboard
- pytest for scanner tests and a minimal verification smoke test

## What I learned

The important design lesson is that an AI-generated fix and a verified fix are not the same thing. A useful security assistant should preserve evidence, label uncertainty, require human review, and be honest about what its tests actually prove.

This is an MVP, not a replacement for mature static-analysis tools. The scanner is heuristic and can miss issues or report false positives. The next steps are more test fixtures, better data-flow-aware rules, structured patch diffs, and stronger sandboxed verification.

## Try it

1. Install Ollama and pull the model listed in the README.
2. Create a Python virtual environment and install `requirements.txt`.
3. Run `python -m pytest -q`.
4. Launch the UI with `streamlit run app.py`.
5. Scan the included intentionally vulnerable demo file and review the results.

Repository: **[add your GitHub repository URL after pushing]**

I built PatchPilot AI to explore how local open-weight models can support developer security workflows without hiding the evidence or pretending AI output is automatically correct.

#hf26 #opensource #python #ai
