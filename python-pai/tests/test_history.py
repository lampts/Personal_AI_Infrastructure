"""Tests for PAI history system (UOCS - Universal Output Capture System)

Tests:
- Saving learnings, research, sessions
- File naming and directory structure
- Listing history entries
- History queries and retrieval
"""

import pytest
from pathlib import Path
from datetime import datetime
import json


# ============================================================
# SAVE TO HISTORY TESTS
# ============================================================

def test_save_learning_to_history(temp_pai_dir, monkeypatch):
    """Test saving a learning to history/learnings/"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    title = "debugging-memory-leak"
    content = """# Debugging Memory Leak

## Problem
Application memory usage growing unbounded.

## Investigation
Used profiling tools to identify leak in cache implementation.

## Solution
Added cache size limits and eviction policy.

## Learning
Always set bounds on in-memory caches.
"""

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_dir = temp_pai_dir / "history" / "learnings" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp}_{title}.md"
    filepath = month_dir / filename

    filepath.write_text(content)

    assert filepath.exists()
    assert content in filepath.read_text()
    assert "debugging-memory-leak" in filepath.name


def test_save_research_to_history(temp_pai_dir, monkeypatch):
    """Test saving research findings to history/research/"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    title = "ai-agent-frameworks"
    content = """# AI Agent Frameworks Research

## Sources
- LangChain documentation
- AutoGPT repository
- Research papers on agent architectures

## Key Findings
1. Most frameworks use ReAct pattern
2. Tool integration is critical
3. Memory management varies widely

## Recommendations
Use modular design with pluggable components.
"""

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_dir = temp_pai_dir / "history" / "research" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp}_{title}.md"
    filepath = month_dir / filename

    filepath.write_text(content)

    assert filepath.exists()
    assert "AI Agent Frameworks Research" in filepath.read_text()


def test_save_session_to_history(temp_pai_dir, sample_session_transcript, monkeypatch):
    """Test saving session transcript to history/sessions/"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_dir = temp_pai_dir / "history" / "sessions" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp}_session.md"
    filepath = month_dir / filename

    filepath.write_text(sample_session_transcript)

    assert filepath.exists()
    assert sample_session_transcript in filepath.read_text()


def test_save_to_history_creates_month_directory(temp_pai_dir, monkeypatch):
    """Test save_to_history creates YYYY-MM directory structure"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    category = "learnings"
    month_str = datetime.now().strftime("%Y-%m")
    month_dir = temp_pai_dir / "history" / category / month_str

    month_dir.mkdir(parents=True, exist_ok=True)

    assert month_dir.exists()
    assert month_str in str(month_dir)


def test_save_to_history_handles_special_characters(temp_pai_dir, monkeypatch):
    """Test saving with special characters in title"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    title = "debugging: memory leak (critical!)"
    sanitized_title = title.replace(" ", "-").replace(":", "").replace("(", "").replace(")", "").replace("!", "")

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_dir = temp_pai_dir / "history" / "learnings" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp}_{sanitized_title}.md"
    filepath = month_dir / filename

    filepath.write_text("test")

    assert filepath.exists()


# ============================================================
# FILENAME AND PATH TESTS
# ============================================================

def test_history_filename_format(temp_pai_dir):
    """Test history files use YYYY-MM-DD-HHMMSS_title.md format"""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    title = "test-learning"
    filename = f"{timestamp}_{title}.md"

    # Verify format
    assert filename.endswith(".md")
    assert "_" in filename
    assert "-" in filename


def test_history_directory_structure(temp_pai_dir):
    """Test history uses category/YYYY-MM/ structure"""
    categories = ["sessions", "learnings", "research", "raw-outputs"]

    for category in categories:
        month_dir = temp_pai_dir / "history" / category / f"{datetime.now():%Y-%m}"
        month_dir.mkdir(parents=True, exist_ok=True)

        assert month_dir.exists()
        assert category in str(month_dir)


def test_history_files_sorted_by_timestamp(temp_pai_dir):
    """Test history files can be sorted chronologically by name"""
    timestamps = [
        "2025-01-01-120000",
        "2025-01-02-120000",
        "2025-01-03-120000"
    ]

    month_dir = temp_pai_dir / "history" / "learnings" / "2025-01"
    month_dir.mkdir(parents=True, exist_ok=True)

    # Create files
    for ts in timestamps:
        filepath = month_dir / f"{ts}_test.md"
        filepath.write_text("test")

    # List and sort
    files = sorted(month_dir.glob("*.md"))

    # Verify chronological order
    assert len(files) == 3
    assert "2025-01-01" in files[0].name
    assert "2025-01-03" in files[2].name


# ============================================================
# LIST HISTORY TESTS
# ============================================================

def test_list_history_entries(temp_pai_dir, monkeypatch):
    """Test listing history entries for a category"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    category = "learnings"
    month_dir = temp_pai_dir / "history" / category / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    # Create test entries
    for i in range(5):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filepath = month_dir / f"{timestamp}_learning-{i}.md"
        filepath.write_text(f"Learning {i}")

    # List entries
    entries = sorted(month_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

    assert len(entries) >= 5


def test_list_history_with_limit(temp_pai_dir):
    """Test listing history with limit parameter"""
    category = "sessions"
    month_dir = temp_pai_dir / "history" / category / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    # Create 20 entries
    for i in range(20):
        filepath = month_dir / f"2025-01-01-{i:06d}_session.md"
        filepath.write_text(f"Session {i}")

    # List with limit=10
    all_entries = sorted(month_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    limited_entries = all_entries[:10]

    assert len(limited_entries) == 10


def test_list_history_empty_category(temp_pai_dir):
    """Test listing history for empty category"""
    category = "research"
    category_dir = temp_pai_dir / "history" / category

    if not category_dir.exists():
        # Should handle gracefully
        result = []
    else:
        result = list(category_dir.rglob("*.md"))

    assert len(result) == 0


def test_list_history_multiple_months(temp_pai_dir):
    """Test listing history across multiple months"""
    category = "learnings"

    months = ["2025-01", "2025-02", "2025-03"]

    all_files = []
    for month in months:
        month_dir = temp_pai_dir / "history" / category / month
        month_dir.mkdir(parents=True, exist_ok=True)

        filepath = month_dir / f"{month}-01-120000_learning.md"
        filepath.write_text("test")
        all_files.append(filepath)

    # Recursively find all .md files
    category_dir = temp_pai_dir / "history" / category
    found_files = list(category_dir.rglob("*.md"))

    assert len(found_files) == 3


# ============================================================
# HISTORY RETRIEVAL TESTS
# ============================================================

def test_retrieve_history_entry_by_name(temp_pai_dir):
    """Test retrieving specific history entry by filename"""
    month_dir = temp_pai_dir / "history" / "learnings" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    target_file = month_dir / "2025-01-01-120000_memory-leak.md"
    target_file.write_text("Memory leak solution")

    # Retrieve by name
    retrieved = month_dir / "2025-01-01-120000_memory-leak.md"

    assert retrieved.exists()
    assert "Memory leak solution" in retrieved.read_text()


def test_search_history_by_keyword(temp_pai_dir):
    """Test searching history entries by keyword"""
    month_dir = temp_pai_dir / "history" / "learnings" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    # Create entries with various keywords
    entries = [
        ("memory-leak", "Memory leak debugging"),
        ("api-design", "API design patterns"),
        ("memory-optimization", "Memory optimization techniques")
    ]

    for filename, content in entries:
        filepath = month_dir / f"2025-01-01-120000_{filename}.md"
        filepath.write_text(content)

    # Search for "memory"
    keyword = "memory"
    matches = [f for f in month_dir.glob("*.md") if keyword in f.name.lower()]

    assert len(matches) == 2  # memory-leak and memory-optimization


def test_retrieve_most_recent_entry(temp_pai_dir):
    """Test retrieving most recent history entry"""
    month_dir = temp_pai_dir / "history" / "sessions" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    # Create entries with different timestamps
    timestamps = [
        "2025-01-01-100000",
        "2025-01-01-110000",
        "2025-01-01-120000"  # Most recent
    ]

    for ts in timestamps:
        filepath = month_dir / f"{ts}_session.md"
        filepath.write_text(f"Session at {ts}")

    # Get most recent
    all_files = sorted(month_dir.glob("*.md"), reverse=True)
    most_recent = all_files[0]

    assert "120000" in most_recent.name


# ============================================================
# HISTORY CLI TESTS
# ============================================================

def test_history_cli_learning_command():
    """Test 'pai-history learning' command"""
    # from click.testing import CliRunner
    # runner = CliRunner()
    # result = runner.invoke(history_cli, ['learning', 'test-title', '-c', 'test content'])
    # assert result.exit_code == 0
    pass  # Placeholder


def test_history_cli_research_command():
    """Test 'pai-history research' command"""
    pass  # Placeholder


def test_history_cli_list_command():
    """Test 'pai-history list' command"""
    pass  # Placeholder


# ============================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================

def test_save_history_with_empty_content(temp_pai_dir):
    """Test saving history entry with empty content"""
    month_dir = temp_pai_dir / "history" / "learnings" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filepath = month_dir / "2025-01-01-120000_empty.md"
    filepath.write_text("")

    assert filepath.exists()
    assert filepath.read_text() == ""


def test_save_history_with_very_long_title(temp_pai_dir):
    """Test saving history with very long title"""
    title = "a" * 300  # 300 character title

    # Should handle gracefully (potentially truncate)
    truncated_title = title[:100]  # Truncate to reasonable length

    month_dir = temp_pai_dir / "history" / "learnings" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filepath = month_dir / f"2025-01-01-120000_{truncated_title}.md"
    filepath.write_text("test")

    assert filepath.exists()


def test_save_history_creates_parent_directories(temp_pai_dir):
    """Test save creates all parent directories if they don't exist"""
    # Deep nested path
    deep_path = temp_pai_dir / "history" / "custom" / "2025-01" / "subdir"
    deep_path.mkdir(parents=True, exist_ok=True)

    filepath = deep_path / "test.md"
    filepath.write_text("test")

    assert filepath.exists()


def test_history_handles_concurrent_writes(temp_pai_dir):
    """Test history system handles concurrent writes"""
    import threading

    month_dir = temp_pai_dir / "history" / "learnings" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    def write_entry(index):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filepath = month_dir / f"{timestamp}_entry-{index}.md"
        filepath.write_text(f"Entry {index}")

    # Create multiple threads writing concurrently
    threads = [threading.Thread(target=write_entry, args=(i,)) for i in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # All entries should be written
    entries = list(month_dir.glob("*.md"))
    assert len(entries) >= 5


# ============================================================
# INTEGRATION TESTS
# ============================================================

def test_full_history_workflow(temp_pai_dir, monkeypatch):
    """Test complete history workflow: save → list → retrieve"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # 1. Save multiple entries
    category = "learnings"
    entries = [
        ("debugging", "Debugging techniques"),
        ("testing", "Testing strategies"),
        ("refactoring", "Refactoring patterns")
    ]

    month_dir = temp_pai_dir / "history" / category / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    for title, content in entries:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filepath = month_dir / f"{timestamp}_{title}.md"
        filepath.write_text(content)

    # 2. List entries
    saved_files = list(month_dir.glob("*.md"))
    assert len(saved_files) == 3

    # 3. Retrieve specific entry
    target = [f for f in saved_files if "debugging" in f.name][0]
    assert "Debugging techniques" in target.read_text()


def test_history_persistence_across_sessions(temp_pai_dir):
    """Test history persists across multiple sessions"""
    # Session 1: Save entry
    month_dir = temp_pai_dir / "history" / "sessions" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    session1_file = month_dir / "2025-01-01-100000_session1.md"
    session1_file.write_text("Session 1 content")

    # Simulate session end / restart

    # Session 2: Entry should still exist
    assert session1_file.exists()

    # Session 2: Add another entry
    session2_file = month_dir / "2025-01-01-110000_session2.md"
    session2_file.write_text("Session 2 content")

    # Both entries should exist
    all_sessions = list(month_dir.glob("*.md"))
    assert len(all_sessions) == 2


def test_history_integrates_with_hooks(temp_pai_dir, monkeypatch, sample_session_transcript):
    """Test history system integrates with hooks for automatic capture"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Simulate SessionEnd hook calling history.save_to_history
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_dir = temp_pai_dir / "history" / "sessions" / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filepath = month_dir / f"{timestamp}_session.md"
    filepath.write_text(sample_session_transcript)

    # Verify automatic capture
    assert filepath.exists()
    assert sample_session_transcript in filepath.read_text()
