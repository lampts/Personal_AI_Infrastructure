#!/usr/bin/env python3
"""PAI History System - Universal Output Capture (UOCS)

Auto-capture:
- Sessions (work logs)
- Learnings (problem-solving)
- Research (investigations)

Usage:
    pai-history learning "debugging-memory-leak" -c "Solution found..."
    pai-history research "ai-agents" -c "Research findings..."
    pai-history list --category sessions --limit 10
"""

import click
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

HISTORY_DIR = Path.home() / ".config" / "pai" / "history"


# ============================================================
# SAVE TO HISTORY
# ============================================================

def save_to_history(category: str, title: str, content: str) -> Path:
    """Save content to history with timestamp

    Args:
        category: Category name (sessions, learnings, research)
        title: Entry title (will be sanitized for filename)
        content: Markdown content to save

    Returns:
        Path: Path to saved file
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")

    # Create month directory
    month_str = datetime.now().strftime("%Y-%m")
    month_dir = HISTORY_DIR / category / month_str
    month_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize title for filename
    safe_title = title.replace(" ", "-").replace("/", "-").replace(":", "")
    safe_title = "".join(c for c in safe_title if c.isalnum() or c in "-_")

    # Create filename
    filename = f"{timestamp}_{safe_title}.md"
    filepath = month_dir / filename

    # Write content
    filepath.write_text(content)

    return filepath


# ============================================================
# LIST HISTORY
# ============================================================

def list_history(category: str, limit: int = 10) -> list[Path]:
    """List history entries for a category

    Args:
        category: Category name
        limit: Maximum number of entries to return

    Returns:
        list: List of file paths, newest first
    """
    category_dir = HISTORY_DIR / category

    if not category_dir.exists():
        return []

    # Find all .md files recursively, sort by modification time
    files = sorted(
        category_dir.rglob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return files[:limit]


# ============================================================
# SEARCH HISTORY
# ============================================================

def search_history(category: str, keyword: str) -> list[Path]:
    """Search history entries by keyword

    Args:
        category: Category name
        keyword: Search keyword (matches filename or content)

    Returns:
        list: List of matching file paths
    """
    category_dir = HISTORY_DIR / category

    if not category_dir.exists():
        return []

    matches = []

    for filepath in category_dir.rglob("*.md"):
        # Check filename
        if keyword.lower() in filepath.name.lower():
            matches.append(filepath)
            continue

        # Check content
        try:
            content = filepath.read_text()
            if keyword.lower() in content.lower():
                matches.append(filepath)
        except Exception:
            # Skip unreadable files
            continue

    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)


# ============================================================
# CLI
# ============================================================

@click.group()
def cli():
    """PAI History Management - Universal Output Capture"""
    pass


@cli.command()
@click.argument("title")
@click.option("--content", "-c", required=True, help="Content to save")
def learning(title: str, content: str):
    """Save a learning to history/learnings/

    Example:
        pai-history learning "debugging-memory-leak" -c "Found issue in cache..."
    """
    path = save_to_history("learnings", title, content)
    click.echo(f"✅ Saved learning: {path}")


@cli.command()
@click.argument("title")
@click.option("--content", "-c", required=True, help="Content to save")
def research(title: str, content: str):
    """Save research findings to history/research/

    Example:
        pai-history research "ai-agent-frameworks" -c "Key findings..."
    """
    path = save_to_history("research", title, content)
    click.echo(f"✅ Saved research: {path}")


@cli.command()
@click.argument("title")
@click.option("--content", "-c", required=True, help="Content to save")
def session(title: str, content: str):
    """Save session notes to history/sessions/

    Example:
        pai-history session "feature-implementation" -c "Session notes..."
    """
    path = save_to_history("sessions", title, content)
    click.echo(f"✅ Saved session: {path}")


@cli.command()
@click.option("--category", "-c", default="sessions", help="Category to list")
@click.option("--limit", "-n", default=10, help="Number of entries to show")
def list(category: str, limit: int):
    """List recent history entries

    Example:
        pai-history list --category learnings --limit 20
    """
    entries = list_history(category, limit)

    if not entries:
        click.echo(f"No {category} found")
        return

    click.echo(f"Recent {category} (showing {len(entries)}):")
    for entry in entries:
        # Show timestamp and title from filename
        filename = entry.stem  # Remove .md extension
        click.echo(f"  {filename}")


@cli.command()
@click.argument("keyword")
@click.option("--category", "-c", default="learnings", help="Category to search")
def search(keyword: str, category: str):
    """Search history by keyword

    Example:
        pai-history search "memory" --category learnings
    """
    matches = search_history(category, keyword)

    if not matches:
        click.echo(f"No matches found for '{keyword}' in {category}")
        return

    click.echo(f"Found {len(matches)} matches for '{keyword}':")
    for match in matches:
        click.echo(f"  {match.stem}")


@cli.command()
@click.argument("filename")
@click.option("--category", "-c", default="learnings", help="Category")
def show(filename: str, category: str):
    """Show content of a history entry

    Example:
        pai-history show 2025-01-01-120000_debugging --category learnings
    """
    category_dir = HISTORY_DIR / category

    # Find file (check with and without .md extension)
    if not filename.endswith(".md"):
        filepath = None
        for file in category_dir.rglob(f"{filename}.md"):
            filepath = file
            break
    else:
        filepath = category_dir / filename

    if not filepath or not filepath.exists():
        click.echo(f"❌ Entry not found: {filename}", err=True)
        return

    # Display content
    content = filepath.read_text()
    click.echo(content)


if __name__ == "__main__":
    cli()
