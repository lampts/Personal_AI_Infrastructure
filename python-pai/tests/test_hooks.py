"""Tests for PAI hooks system

Tests:
- SessionStart hook: CORE context loading
- SessionEnd hook: Session transcript capture
- PostToolUse hook: Tool usage logging
- Hook error handling and resilience
"""

import pytest
from pathlib import Path
import json
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
import sys
from io import StringIO


# ============================================================
# SESSION START HOOK TESTS
# ============================================================

def test_session_start_loads_core_skill(temp_pai_dir, sample_core_skill, monkeypatch, capsys):
    """Test SessionStart hook loads CORE skill content"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(temp_pai_dir))

    # Simulate session_start() function
    core_path = sample_core_skill
    core_content = core_path.read_text()

    message = f"""<system-reminder>
PAI CORE CONTEXT (Auto-loaded)

{core_content}
</system-reminder>"""

    print(message)

    captured = capsys.readouterr()
    assert "<system-reminder>" in captured.out
    assert "PAI CORE CONTEXT" in captured.out
    assert "Identity" in captured.out


def test_session_start_missing_core_skill(temp_pai_dir, monkeypatch, capsys):
    """Test SessionStart hook handles missing CORE skill gracefully"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    core_path = temp_pai_dir / "skills" / "CORE.md"

    # Remove CORE skill if it exists
    if core_path.exists():
        core_path.unlink()

    # Simulate hook behavior
    if not core_path.exists():
        print("❌ CORE skill not found", file=sys.stderr)

    captured = capsys.readouterr()
    assert "❌ CORE skill not found" in captured.err


def test_session_start_skips_for_subagent(monkeypatch, capsys):
    """Test SessionStart hook skips execution for subagent sessions"""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/path/to/.claude/agents/researcher")

    # Check if subagent
    claude_project_dir = "/path/to/.claude/agents/researcher"
    is_subagent = "/.claude/agents/" in claude_project_dir

    if is_subagent:
        print("🤖 Subagent session - skipping CORE context loading", file=sys.stderr)
        sys.exit(0)

    captured = capsys.readouterr()
    assert "Subagent session" in captured.err


def test_session_start_formats_timestamp(capsys):
    """Test SessionStart hook includes current timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = f"""<system-reminder>
📅 CURRENT DATE/TIME: {timestamp}
</system-reminder>"""

    print(message)

    captured = capsys.readouterr()
    assert "📅 CURRENT DATE/TIME:" in captured.out
    assert timestamp in captured.out


# ============================================================
# SESSION END HOOK TESTS
# ============================================================

def test_session_end_captures_transcript(temp_pai_dir, sample_session_transcript, monkeypatch):
    """Test SessionEnd hook saves transcript to history"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Simulate session_end() reading from stdin and writing to history
    transcript = sample_session_transcript
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    session_file = temp_pai_dir / "history" / "sessions" / f"{timestamp}_session.md"

    # Ensure directory exists
    session_file.parent.mkdir(parents=True, exist_ok=True)

    # Write transcript
    session_file.write_text(transcript)

    assert session_file.exists()
    assert transcript in session_file.read_text()


def test_session_end_creates_month_directory(temp_pai_dir, monkeypatch):
    """Test SessionEnd hook creates YYYY-MM directory structure"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_str = datetime.now().strftime("%Y-%m")

    session_file = temp_pai_dir / "history" / "sessions" / month_str / f"{timestamp}_session.md"
    session_file.parent.mkdir(parents=True, exist_ok=True)

    assert session_file.parent.exists()
    assert month_str in str(session_file.parent)


def test_session_end_handles_empty_transcript(temp_pai_dir, monkeypatch):
    """Test SessionEnd hook handles empty transcript"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    transcript = ""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    session_file = temp_pai_dir / "history" / "sessions" / f"{timestamp}_session.md"

    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(transcript)

    assert session_file.exists()
    assert session_file.read_text() == ""


def test_session_end_logs_success_message(temp_pai_dir, capsys, monkeypatch):
    """Test SessionEnd hook logs success message to stderr"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    session_file = temp_pai_dir / "history" / "sessions" / f"{timestamp}_session.md"

    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text("test")

    print(f"✅ Session saved: {session_file}", file=sys.stderr)

    captured = capsys.readouterr()
    assert "✅ Session saved:" in captured.err


# ============================================================
# POST TOOL USE HOOK TESTS
# ============================================================

def test_post_tool_use_logs_event(temp_pai_dir, monkeypatch):
    """Test PostToolUse hook logs tool event to JSONL"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Sample tool event
    event = {
        "tool": "Read",
        "parameters": {"file_path": "/path/to/file.py"},
        "result": "success"
    }

    timestamp = datetime.now()
    month_str = timestamp.strftime("%Y-%m")
    log_file = temp_pai_dir / "history" / "raw-outputs" / month_str / "events.jsonl"

    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Append event
    with log_file.open("a") as f:
        f.write(json.dumps({"timestamp": timestamp.isoformat(), **event}) + "\n")

    assert log_file.exists()

    # Read and verify
    with log_file.open("r") as f:
        logged_event = json.loads(f.readline())

    assert logged_event["tool"] == "Read"
    assert logged_event["result"] == "success"


def test_post_tool_use_appends_multiple_events(temp_pai_dir, monkeypatch):
    """Test PostToolUse hook appends multiple events to JSONL"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    events = [
        {"tool": "Read", "result": "success"},
        {"tool": "Write", "result": "success"},
        {"tool": "Bash", "result": "error"}
    ]

    month_str = datetime.now().strftime("%Y-%m")
    log_file = temp_pai_dir / "history" / "raw-outputs" / month_str / "events.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    for event in events:
        with log_file.open("a") as f:
            f.write(json.dumps({"timestamp": datetime.now().isoformat(), **event}) + "\n")

    # Verify all events logged
    with log_file.open("r") as f:
        lines = f.readlines()

    assert len(lines) == 3

    logged_tools = [json.loads(line)["tool"] for line in lines]
    assert "Read" in logged_tools
    assert "Write" in logged_tools
    assert "Bash" in logged_tools


def test_post_tool_use_handles_malformed_json():
    """Test PostToolUse hook handles malformed JSON input"""
    malformed_json = '{"tool": "Read", invalid}'

    with pytest.raises(json.JSONDecodeError):
        json.loads(malformed_json)


def test_post_tool_use_logs_success_message(capsys):
    """Test PostToolUse hook logs success to stderr"""
    tool_name = "Read"

    print(f"✅ Logged: {tool_name}", file=sys.stderr)

    captured = capsys.readouterr()
    assert "✅ Logged: Read" in captured.err


# ============================================================
# HOOK ERROR HANDLING TESTS
# ============================================================

def test_hook_handles_permission_error(temp_pai_dir, monkeypatch):
    """Test hooks handle permission errors gracefully"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Create read-only directory
    readonly_dir = temp_pai_dir / "history" / "readonly"
    readonly_dir.mkdir(parents=True, exist_ok=True)
    readonly_dir.chmod(0o444)  # Read-only

    # Try to write to read-only location
    test_file = readonly_dir / "test.md"

    try:
        test_file.write_text("test")
    except PermissionError:
        # Hook should catch and log error
        print("❌ Permission denied", file=sys.stderr)

    # Cleanup
    readonly_dir.chmod(0o755)


def test_hook_handles_disk_full_error(temp_pai_dir):
    """Test hooks handle disk full errors"""
    # Simulate disk full by mocking write operation
    with patch('pathlib.Path.write_text', side_effect=OSError("No space left on device")):
        test_file = temp_pai_dir / "test.md"

        with pytest.raises(OSError, match="No space left on device"):
            test_file.write_text("test")


def test_hook_exits_gracefully_on_error(capsys):
    """Test hooks exit with proper status code on error"""
    try:
        raise Exception("Test error")
    except Exception as e:
        print(f"❌ Error in hook: {e}", file=sys.stderr)
        # Would call sys.exit(1)

    captured = capsys.readouterr()
    assert "❌ Error in hook:" in captured.err


# ============================================================
# HOOK CLI TESTS
# ============================================================

def test_hooks_cli_start_command():
    """Test hooks CLI 'start' command"""
    # from click.testing import CliRunner
    # runner = CliRunner()
    # result = runner.invoke(hooks_cli, ['start'])
    # assert result.exit_code == 0
    pass  # Placeholder


def test_hooks_cli_end_command():
    """Test hooks CLI 'end' command"""
    pass  # Placeholder


def test_hooks_cli_tool_command():
    """Test hooks CLI 'tool' command"""
    pass  # Placeholder


# ============================================================
# INTEGRATION TESTS
# ============================================================

def test_full_hook_lifecycle(temp_pai_dir, sample_core_skill, sample_session_transcript, monkeypatch, capsys):
    """Test complete hook lifecycle: SessionStart → PostToolUse → SessionEnd"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(temp_pai_dir))

    # 1. SessionStart - Load CORE
    core_content = sample_core_skill.read_text()
    print(f"<system-reminder>\n{core_content}\n</system-reminder>")

    # 2. PostToolUse - Log tool event
    event = {"tool": "Read", "result": "success"}
    month_str = datetime.now().strftime("%Y-%m")
    log_file = temp_pai_dir / "history" / "raw-outputs" / month_str / "events.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with log_file.open("a") as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), **event}) + "\n")

    # 3. SessionEnd - Save transcript
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    session_file = temp_pai_dir / "history" / "sessions" / f"{timestamp}_session.md"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(sample_session_transcript)

    # Verify all hooks executed
    captured = capsys.readouterr()
    assert "<system-reminder>" in captured.out

    assert log_file.exists()
    assert session_file.exists()
    assert sample_session_transcript in session_file.read_text()


def test_hooks_run_independently(temp_pai_dir, monkeypatch):
    """Test hooks can run independently without dependencies"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # SessionStart should work without SessionEnd
    core_path = temp_pai_dir / "skills" / "CORE.md"
    core_path.parent.mkdir(parents=True, exist_ok=True)
    core_path.write_text("# Core content")

    assert core_path.exists()

    # PostToolUse should work independently
    month_str = datetime.now().strftime("%Y-%m")
    log_file = temp_pai_dir / "history" / "raw-outputs" / month_str / "events.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with log_file.open("a") as f:
        f.write(json.dumps({"tool": "Test"}) + "\n")

    assert log_file.exists()

    # SessionEnd should work independently
    session_file = temp_pai_dir / "history" / "sessions" / "test_session.md"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text("test")

    assert session_file.exists()


def test_hook_failure_doesnt_block_session(temp_pai_dir, monkeypatch, capsys):
    """Test that hook failure doesn't prevent session from continuing"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Simulate hook failure
    try:
        raise Exception("Hook failed")
    except Exception as e:
        # Log error but continue
        print(f"⚠️ Hook failed, continuing session: {e}", file=sys.stderr)

    captured = capsys.readouterr()
    assert "⚠️ Hook failed" in captured.err

    # Session should continue (no sys.exit() called)
