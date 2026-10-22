from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st

from patchpilot.ai_engine import DEFAULT_MODEL, diagnose_with_ollama
from patchpilot.scanner import scan_python
from patchpilot.verifier import verify_candidate

st.set_page_config(page_title="PatchPilot AI | Security Workbench", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --pp-bg:#070b16; --pp-panel:rgba(17,25,45,.78); --pp-panel2:#101a2d; --pp-border:rgba(127,160,212,.18); --pp-text:#edf4ff; --pp-muted:#91a4c4; --pp-cyan:#39e6ff; --pp-purple:#a78bfa; --pp-green:#75f0b5; --pp-red:#ff6687; }
html, body, [data-testid="stAppViewContainer"] { background: radial-gradient(ellipse at 15% 0%, #16244a 0%, #080d1b 38%, #060913 100%) !important; color:var(--pp-text) !important; font-family:'Manrope',sans-serif !important; }
[data-testid="stHeader"] { background:transparent !important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,rgba(12,20,38,.98),rgba(7,11,22,.98)) !important; border-right:1px solid var(--pp-border); }
[data-testid="stSidebar"] * { color:var(--pp-text); }
.block-container { padding-top:1.5rem !important; padding-bottom:3rem !important; max-width:1500px; }
#MainMenu, footer { visibility:hidden; }
.pp-hero { position:relative; overflow:hidden; padding:28px 30px; border:1px solid rgba(75,218,255,.25); border-radius:24px; background:linear-gradient(125deg,rgba(17,35,66,.94),rgba(22,18,49,.80)); box-shadow:0 18px 60px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.06); margin-bottom:20px; }
.pp-hero:after { content:''; position:absolute; right:-90px; top:-130px; width:340px; height:340px; border-radius:50%; background:radial-gradient(circle,rgba(57,230,255,.16),rgba(167,139,250,.08) 45%,transparent 70%); pointer-events:none; }
.pp-kicker { color:var(--pp-cyan); font:500 11px 'DM Mono',monospace; letter-spacing:2.3px; text-transform:uppercase; }
.pp-title { font-size:clamp(30px,4vw,48px); font-weight:800; letter-spacing:-2px; line-height:1.06; margin:12px 0 10px; color:#f4f8ff; }
.pp-title span { background:linear-gradient(90deg,#42eaff,#b7a3ff); -webkit-background-clip:text; color:transparent; }
.pp-sub { color:#a8b8d4; font-size:14px; line-height:1.65; max-width:660px; }
.pp-chip { display:inline-flex; gap:7px; align-items:center; border:1px solid rgba(117,240,181,.24); background:rgba(117,240,181,.08); border-radius:999px; color:#9af7ca; padding:7px 11px; font:11px 'DM Mono',monospace; }
.pp-section { color:#eef4ff; font-size:15px; font-weight:800; letter-spacing:-.2px; margin:7px 0 12px; }
.pp-section small { color:var(--pp-muted); font:11px 'DM Mono',monospace; letter-spacing:1px; margin-left:8px; }
.pp-card { border:1px solid var(--pp-border); background:linear-gradient(145deg,rgba(20,31,54,.82),rgba(11,18,34,.86)); border-radius:18px; padding:17px 18px; min-height:106px; box-shadow:0 10px 30px rgba(0,0,0,.14),inset 0 1px 0 rgba(255,255,255,.035); }
.pp-metric-label { color:#91a4c4; font:11px 'DM Mono',monospace; letter-spacing:1.2px; text-transform:uppercase; }
.pp-metric-value { color:#f3f7ff; font-size:29px; font-weight:800; margin-top:10px; letter-spacing:-1px; }
.pp-metric-note { color:#7f94b7; font-size:11px; margin-top:3px; }
.pp-pill { display:inline-block; font:10px 'DM Mono',monospace; letter-spacing:.7px; padding:5px 8px; border-radius:6px; margin-right:5px; border:1px solid rgba(255,255,255,.12); }
.pp-critical { color:#ff8ba2; background:rgba(255,102,135,.1); border-color:rgba(255,102,135,.25); }
.pp-high { color:#ffc17e; background:rgba(255,174,102,.09); border-color:rgba(255,174,102,.22); }
.pp-medium { color:#ffe78a; background:rgba(255,231,138,.08); border-color:rgba(255,231,138,.2); }
.pp-low { color:#8ce9c4; background:rgba(117,240,181,.08); border-color:rgba(117,240,181,.2); }
.pp-step { display:flex; gap:12px; align-items:center; padding:12px 13px; border:1px solid var(--pp-border); border-radius:13px; background:rgba(15,24,43,.7); margin:8px 0; }
.pp-step-num { width:31px;height:31px; flex:0 0 31px; display:grid; place-items:center; border-radius:10px; color:var(--pp-cyan); background:rgba(57,230,255,.09); border:1px solid rgba(57,230,255,.18); font:12px 'DM Mono',monospace; }
.pp-step-title { font-weight:700; font-size:12px; }
.pp-step-sub { font-size:11px; color:#8fa2c2; margin-top:3px; }
.pp-live { display:inline-block; width:7px;height:7px;border-radius:50%;background:#75f0b5;box-shadow:0 0 12px #75f0b5;margin-right:7px; }
.stTextArea textarea, .stTextInput input { background:#080f20 !important; color:#e7f1ff !important; border:1px solid rgba(123,155,210,.24) !important; border-radius:12px !important; font-family:'DM Mono',monospace !important; font-size:12px !important; }
.stTextArea textarea:focus, .stTextInput input:focus { border-color:rgba(57,230,255,.7) !important; box-shadow:0 0 0 1px rgba(57,230,255,.2) !important; }
.stButton>button { border-radius:11px !important; border:1px solid rgba(57,230,255,.38) !important; background:linear-gradient(100deg,rgba(34,190,218,.18),rgba(130,98,240,.2)) !important; color:#e9faff !important; font-weight:800 !important; transition:all .2s ease !important; }
.stButton>button:hover { border-color:var(--pp-cyan) !important; box-shadow:0 0 24px rgba(57,230,255,.15) !important; transform:translateY(-1px); }
.stDownloadButton>button { border-radius:10px !important; }
[data-testid="stExpander"] { background:rgba(13,21,39,.7); border:1px solid var(--pp-border); border-radius:13px; }
[data-testid="stMetric"] { background:rgba(17,25,45,.75); padding:14px; border:1px solid var(--pp-border); border-radius:14px; }
[data-testid="stCode"] { border:1px solid var(--pp-border); border-radius:12px; }
hr { border-color:rgba(127,160,212,.14) !important; }
@keyframes pulseGlow { 0%,100% { opacity:.7; box-shadow:0 0 0 rgba(57,230,255,0); } 50% { opacity:1; box-shadow:0 0 16px rgba(57,230,255,.13); } }
.pp-chip { animation:pulseGlow 3s ease-in-out infinite; }
@media (max-width:700px) { .pp-hero { padding:22px 18px; } .pp-title { letter-spacing:-1.3px; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

SAMPLE = '''import subprocess\n\ndef lookup_host(host):\n    # Vulnerable: shell command includes a value that may be user-controlled.\n    return subprocess.run("ping -c 1 " + host, shell=True, capture_output=True, text=True)\n\nuser_expression = "2 + 2"\nprint(eval(user_expression))\n'''

if "source_code" not in st.session_state:
    st.session_state.source_code = SAMPLE
if "findings" not in st.session_state:
    st.session_state.findings = []
if "ai_report" not in st.session_state:
    st.session_state.ai_report = ""
if "candidate_code" not in st.session_state:
    st.session_state.candidate_code = ""
if "verification" not in st.session_state:
    st.session_state.verification = None

with st.sidebar:
    st.markdown("<div class='pp-kicker'>PATCHPILOT / WORKSPACE</div>", unsafe_allow_html=True)
    st.markdown("## 🛡️ PatchPilot AI")
    st.caption("Local-first security workbench")
    st.markdown("---")
    st.markdown("<span class='pp-live'></span>LOCAL MODEL", unsafe_allow_html=True)
    model = st.text_input("Ollama model tag", value=DEFAULT_MODEL, help="Must already be available locally in Ollama.")
    st.caption("No proprietary AI API. Source is sent only to your local Ollama service when you request an AI diagnosis.")
    st.markdown("---")
    st.markdown("**SCAN RULES**")
    st.markdown("`PP001` Dynamic eval/exec\n\n`PP002` Shell injection risk\n\n`PP003` Hardcoded credential heuristic\n\n`PP004` Pickle deserialization\n\n`PP005` Unsafe YAML loading\n\n`PP006` Security assert")
    st.markdown("---")
    st.caption("MVP • Heuristic scanner • Review all AI suggestions")

st.markdown("""
<div class="pp-hero">
  <div class="pp-kicker">✳ OPEN-WEIGHT AI · LOCAL-FIRST SECURITY</div>
  <div class="pp-title">Find it. <span>Fix it.</span><br>Prove it.</div>
  <div class="pp-sub">A security workbench for Python code. Detect risky patterns with AST analysis, ask a local open-weight model for a grounded remediation plan, and verify a candidate without silently applying changes.</div>
  <div style="margin-top:18px"><span class="pp-chip">● LOCAL AI PIPELINE</span> &nbsp; <span class="pp-chip" style="color:#c8baff;border-color:rgba(167,139,250,.25);background:rgba(167,139,250,.08)">AST-POWERED SCANNING</span></div>
</div>
""", unsafe_allow_html=True)

# Workflow strip
cols = st.columns(4)
steps = [("01", "AST SCAN", "Static analysis"), ("02", "AI EXPLAIN", "Local Ollama model"), ("03", "VERIFY", "Syntax + optional pytest"), ("04", "REPORT", "Export evidence")]
for col, (num, title, subtitle) in zip(cols, steps):
    with col:
        st.markdown(f"<div class='pp-step'><div class='pp-step-num'>{num}</div><div><div class='pp-step-title'>{title}</div><div class='pp-step-sub'>{subtitle}</div></div></div>", unsafe_allow_html=True)

st.markdown("<div class='pp-section'>01 / TARGET CODE INPUT <small>PASTE OR LOAD A LOCAL FILE</small></div>", unsafe_allow_html=True)
source_upload = st.file_uploader("Upload a Python file (.py)", type=["py"], help="The file is read into this session; it is not uploaded to a remote service.")
if source_upload is not None:
    try:
        st.session_state.source_code = source_upload.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error("This file is not valid UTF-8 text.")

left, right = st.columns([1.45, .75], gap="large")
with left:
    st.session_state.source_code = st.text_area("Target Python source", value=st.session_state.source_code, height=300, label_visibility="collapsed", key="source_editor")
    scan_col, reset_col = st.columns([1, 1])
    with scan_col:
        scan_clicked = st.button("⌁  Run AST Security Scan", use_container_width=True, type="primary")
    with reset_col:
        if st.button("↺  Load demo sample", use_container_width=True):
            st.session_state.source_code = SAMPLE
            st.session_state.source_editor = SAMPLE
            st.session_state.findings = []
            st.session_state.ai_report = ""
            st.session_state.candidate_code = ""
            st.session_state.verification = None
            st.rerun()
with right:
    st.markdown("<div class='pp-card'><div class='pp-metric-label'>SCAN ENGINE</div><div class='pp-metric-value' style='font-size:21px'>Python AST</div><div class='pp-metric-note'>Structure-aware checks + conservative secret patterns</div><hr><div class='pp-metric-label'>DATA BOUNDARY</div><div style='font-size:13px;font-weight:700;margin-top:8px'>Your code stays local</div><div class='pp-metric-note'>Only an explicit AI request sends code to localhost Ollama.</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='pp-card' style='margin-top:12px'><div class='pp-metric-label'>IMPORTANT</div><div style='font-size:12px;line-height:1.7;color:#b4c3dc;margin-top:9px'>Findings are heuristic, not proof of exploitability. Never paste production secrets. Review any suggested patch before using it.</div></div>", unsafe_allow_html=True)

if scan_clicked:
    st.session_state.findings = [f.to_dict() for f in scan_python(st.session_state.source_code)]
    st.session_state.ai_report = ""
    st.session_state.verification = None

findings = st.session_state.findings
counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]}

st.markdown("<div class='pp-section'>02 / AST SCANNING STATUS <small>FINDINGS & EVIDENCE</small></div>", unsafe_allow_html=True)
metrics = st.columns(4)
metric_data = [("TOTAL FINDINGS", len(findings), "Current scan"), ("CRITICAL / HIGH", counts["CRITICAL"] + counts["HIGH"], "Prioritize first"), ("MEDIUM", counts["MEDIUM"], "Review context"), ("LOW / INFO", counts["LOW"] + counts["INFO"], "Hardening signals")]
for col, (label, value, note) in zip(metrics, metric_data):
    with col:
        st.markdown(f"<div class='pp-card'><div class='pp-metric-label'>{label}</div><div class='pp-metric-value'>{value}</div><div class='pp-metric-note'>{note}</div></div>", unsafe_allow_html=True)

if not findings:
    st.info("No scan results yet. Click **Run AST Security Scan** to inspect the target code. An empty result does not prove the code is secure.")
else:
    for f in findings:
        severity_class = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(f["severity"], "low")
        with st.expander(f"{f['severity']}  ·  {f['rule_id']}  ·  Line {f['line']} — {f['title']}", expanded=f["severity"] in {"CRITICAL", "HIGH"}):
            st.markdown(f"<span class='pp-pill pp-{severity_class}'>{html.escape(f['severity'])}</span> <span class='pp-pill'>{html.escape(f['rule_id'])}</span> <span class='pp-pill'>LINE {f['line']}</span>", unsafe_allow_html=True)
            st.code(f["evidence"], language="python")
            st.write(f["explanation"])
            st.markdown("**Recommended direction**")
            st.write(f["recommendation"])

st.markdown("<div class='pp-section'>03 / AI PATCH GENERATION <small>LOCAL OPEN-WEIGHT MODEL</small></div>", unsafe_allow_html=True)
st.caption(f"Selected model: `{model}` · Ollama must be running locally and the model must already be pulled.")
if st.button("✦  Explain findings with local AI", disabled=not bool(findings), use_container_width=False):
    with st.spinner("Asking your local model for an evidence-grounded review…"):
        try:
            st.session_state.ai_report = diagnose_with_ollama(st.session_state.source_code, findings, model=model)
        except Exception as exc:
            st.session_state.ai_report = "LOCAL MODEL ERROR: " + str(exc)
if st.session_state.ai_report:
    st.markdown(st.session_state.ai_report)
    st.caption("AI output is a suggestion, not a verified patch. Do not auto-apply it.")

st.markdown("**Candidate code for verification**")
st.caption("Paste your reviewed, manually edited candidate code here. PatchPilot will not silently edit your source.")
st.session_state.candidate_code = st.text_area("Candidate code", value=st.session_state.candidate_code, height=220, key="candidate_editor", label_visibility="collapsed", placeholder="Paste a candidate fix here…")
verify_col, pytest_col = st.columns([1, 1])
with verify_col:
    if st.button("✓  Check Python syntax", use_container_width=True):
        st.session_state.verification = verify_candidate(st.session_state.candidate_code, run_pytest=False).to_dict() if st.session_state.candidate_code.strip() else {"syntax_ok": False, "pytest_ran": False, "pytest_exit_code": None, "output": "Paste candidate code first.", "warning": "No code was verified."}
with pytest_col:
    run_tests = st.checkbox("I understand pytest may execute code I trust", value=False)
    if st.button("▶  Run isolated MVP pytest", use_container_width=True, disabled=not run_tests):
        st.session_state.verification = verify_candidate(st.session_state.candidate_code, run_pytest=True).to_dict() if st.session_state.candidate_code.strip() else {"syntax_ok": False, "pytest_ran": False, "pytest_exit_code": None, "output": "Paste candidate code first.", "warning": "No code was verified."}

if st.session_state.verification:
    result = st.session_state.verification
    status = "PASS" if result["syntax_ok"] and (not result["pytest_ran"] or result["pytest_exit_code"] == 0) else "REVIEW"
    st.markdown(f"<div class='pp-card'><div class='pp-metric-label'>VERIFICATION STATUS</div><div class='pp-metric-value' style='font-size:24px;color:{'#75f0b5' if status == 'PASS' else '#ffb879'}'>{status}</div><div class='pp-metric-note'>{'Syntax passed' if result['syntax_ok'] else 'Syntax failed'} · {'pytest ran' if result['pytest_ran'] else 'pytest not run'}</div></div>", unsafe_allow_html=True)
    st.code(result["output"])
    st.warning(result["warning"])

st.markdown("<div class='pp-section'>04 / EXPORT REPORT <small>REPRODUCIBLE EVIDENCE</small></div>", unsafe_allow_html=True)
report = {"project": "PatchPilot AI", "scanner": "Python AST + heuristic patterns", "findings": findings, "ai_review": st.session_state.ai_report, "verification": st.session_state.verification, "disclaimer": "Heuristic results are not a guarantee of security. AI advice is not a verified patch."}
report_json = json.dumps(report, indent=2, ensure_ascii=False)
st.download_button("↓  Export scan report (JSON)", data=report_json, file_name="patchpilot-report.json", mime="application/json", disabled=not bool(findings))
st.markdown("<div style='margin-top:30px;padding:16px;border-top:1px solid rgba(127,160,212,.15);color:#7f93b5;font-size:11px;font-family:DM Mono,monospace'>PATCHPILOT AI / OPEN SOURCE SECURITY WORKBENCH / LOCAL-FIRST BY DESIGN</div>", unsafe_allow_html=True)
