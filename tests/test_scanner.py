from patchpilot.scanner import scan_python


def test_detects_eval():
    findings = scan_python("result = eval(user_input)\n")
    assert any(item.rule_id == "PP001" for item in findings)


def test_detects_shell_true():
    source = "import subprocess\nsubprocess.run('echo ' + value, shell=True)\n"
    findings = scan_python(source)
    assert any(item.rule_id == "PP002" for item in findings)


def test_detects_secret_assignment_without_exposing_value():
    findings = scan_python("api_key = 'supersecretvalue123'\n")
    secret_findings = [item for item in findings if item.rule_id == "PP003"]
    assert secret_findings
    assert "supersecretvalue123" not in secret_findings[0].evidence


def test_syntax_error_is_reported():
    findings = scan_python("def broken(:\n")
    assert findings and findings[0].rule_id == "PP000"
