#!/usr/bin/env python3
"""PAI Hook System - Event-driven automation

Hooks fire on Claude Code lifecycle events:
- SessionStart: Load CORE context
- SessionEnd: Capture session summary
- PostToolUse: Log tool usage

Usage:
    pai-hooks start      # SessionStart
    pai-hooks end        # SessionEnd
    pai-hooks tool       # PostToolUse
"""

import sys
import json
import click
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

PAI_DIR = Path.home() / ".config" / "pai"
SKILLS_DIR = PAI_DIR / "skills"
HISTORY_DIR = PAI_DIR / "history"


# ============================================================
# HOOK: SessionStart
# ============================================================

def session_start():
    """Load CORE skill context at session start

    Reads CORE.md and outputs as system-reminder for Claude to ingest.
    Skips execution for subagent sessions.
    """
    # Check if this is a subagent session
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    is_subagent = "/.claude/agents/" in claude_project_dir or \
                  os.environ.get("CLAUDE_AGENT_TYPE") is not None

    if is_subagent:
        print("🤖 Subagent session - skipping CORE context loading", file=sys.stderr)
        return 0

    # Load CORE skill
    core_path = SKILLS_DIR / "CORE.md"

    if not core_path.exists():
        print(f"❌ CORE skill not found at: {core_path}", file=sys.stderr)
        print(f"💡 Run: pai init", file=sys.stderr)
        return 1

    print("📚 Reading CORE context from skill file...", file=sys.stderr)

    # Read CORE content
    core_content = core_path.read_text()

    print(f"✅ Read {len(core_content)} characters from CORE.md", file=sys.stderr)

    # Get current timestamp
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # Output as system-reminder (Claude Code will ingest this)
    message = f"""<system-reminder>
PAI CORE CONTEXT (Auto-loaded at Session Start)

📅 CURRENT DATE/TIME: {timestamp}

The following context has been loaded from {core_path}:

---
{core_content}
---

This context is now active for this session. Follow all instructions, preferences, and guidelines contained above.
</system-reminder>"""

    # Write to stdout (captured by Claude Code)
    print(message)

    print("✅ CORE context injected into session", file=sys.stderr)
    return 0


# ============================================================
# HOOK: SessionEnd
# ============================================================

def session_end():
    """Capture session summary to history

    Reads transcript from stdin and saves to history/sessions/
    """
    # Read transcript from stdin
    transcript = sys.stdin.read()

    # Generate timestamp-based filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_str = datetime.now().strftime("%Y-%m")

    # Create month directory
    session_dir = HISTORY_DIR / "sessions" / month_str
    session_dir.mkdir(parents=True, exist_ok=True)

    # Write transcript
    session_file = session_dir / f"{timestamp}_session.md"
    session_file.write_text(transcript)

    print(f"✅ Session saved: {session_file}", file=sys.stderr)
    return 0


# ============================================================
# HOOK: PostToolUse
# ============================================================

def post_tool_use():
    """Log tool usage to database

    Reads tool event JSON from stdin and appends to JSONL log.
    """
    try:
        # Read tool event from stdin (JSON)
        event_json = sys.stdin.read()

        if not event_json.strip():
            print("⚠️ No event data received", file=sys.stderr)
            return 1

        event = json.loads(event_json)

        # Extract key info
        tool_name = event.get("tool", "unknown")
        timestamp = datetime.now().isoformat()

        # Create month directory
        month_str = datetime.now().strftime("%Y-%m")
        log_dir = HISTORY_DIR / "raw-outputs" / month_str
        log_dir.mkdir(parents=True, exist_ok=True)

        # Append to JSONL log
        log_file = log_dir / "events.jsonl"

        with log_file.open("a") as f:
            log_entry = {"timestamp": timestamp, **event}
            f.write(json.dumps(log_entry) + "\n")

        print(f"✅ Logged: {tool_name}", file=sys.stderr)
        return 0

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"❌ Error logging event: {e}", file=sys.stderr)
        return 1


# ============================================================
# CLI
# ============================================================

@click.group()
def cli():
    """PAI Hook System - Event-driven automation"""
    pass


@cli.command()
def start():
    """SessionStart hook - Load CORE context"""
    sys.exit(session_start())


@cli.command()
def end():
    """SessionEnd hook - Capture session summary"""
    sys.exit(session_end())


@cli.command()
def tool():
    """PostToolUse hook - Log tool usage"""
    sys.exit(post_tool_use())


if __name__ == "__main__":
    import os  # Import here to avoid issues during module loading
    cli()
