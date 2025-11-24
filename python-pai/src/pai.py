#!/usr/bin/env python3
"""PAI - Personal AI Infrastructure CLI

Minimal Python implementation combining Unix philosophy, Karpathy code quality,
and Simon Willison's LLM design patterns.

Usage:
    pai ask "research quantum computing"
    pai skills
    pai show research
"""

import click
import yaml
from pathlib import Path
from anthropic import Anthropic
from typing import Optional

# ============================================================
# CONFIGURATION
# ============================================================

PAI_DIR = Path.home() / ".config" / "pai"
SKILLS_DIR = PAI_DIR / "skills"
AGENTS_DIR = PAI_DIR / "agents"
CONFIG_PATH = PAI_DIR / "config.yaml"


def load_config() -> dict:
    """Load user configuration from config.yaml

    Returns:
        dict: Configuration with API keys and preferences
    """
    if not CONFIG_PATH.exists():
        return {
            "anthropic_api_key": None,
            "default_model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096
        }

    return yaml.safe_load(CONFIG_PATH.read_text())


def load_skill(name: str) -> str:
    """Load skill markdown content by name

    Args:
        name: Skill name (e.g., "CORE", "research")

    Returns:
        str: Full skill markdown content

    Raises:
        FileNotFoundError: If skill file doesn't exist
    """
    skill_path = SKILLS_DIR / f"{name}.md"

    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {name}")

    return skill_path.read_text()


# ============================================================
# SKILL ROUTING (Natural Language → Skill)
# ============================================================

def route_to_skill(user_input: str) -> str:
    """Route user input to appropriate skill using trigger matching

    Args:
        user_input: Natural language user request

    Returns:
        str: Skill name to load (defaults to "CORE")
    """
    # Scan all skills for trigger matches
    for skill_file in SKILLS_DIR.glob("*.md"):
        content = skill_file.read_text()

        # Extract YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                _, frontmatter, _ = parts
                try:
                    meta = yaml.safe_load(frontmatter)

                    # Check if user input matches any trigger
                    triggers = meta.get("triggers", [])
                    for trigger in triggers:
                        if trigger.lower() in user_input.lower():
                            return skill_file.stem

                except yaml.YAMLError:
                    # Skip malformed frontmatter
                    continue

    # Default to CORE skill
    return "CORE"


# ============================================================
# LLM EXECUTION
# ============================================================

def execute_with_skill(user_input: str, skill_name: str, config: dict) -> str:
    """Execute user request with skill context loaded

    Args:
        user_input: User's natural language request
        skill_name: Name of skill to use for context
        config: Configuration dict with API keys

    Returns:
        str: Claude's response text

    Raises:
        Exception: If API call fails
    """
    # Load skill content
    skill_content = load_skill(skill_name)

    # Initialize Anthropic client
    client = Anthropic(api_key=config["anthropic_api_key"])

    # Build messages with skill context
    messages = [
        {
            "role": "user",
            "content": f"<skill-context>\n{skill_content}\n</skill-context>\n\n{user_input}"
        }
    ]

    # Call Claude API
    response = client.messages.create(
        model=config.get("default_model", "claude-sonnet-4-5-20250929"),
        max_tokens=config.get("max_tokens", 4096),
        messages=messages
    )

    return response.content[0].text


# ============================================================
# CLI COMMANDS
# ============================================================

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PAI - Personal AI Infrastructure

    Minimal Python implementation for skill-based AI workflows.
    """
    pass


@cli.command()
@click.argument("prompt")
@click.option("--skill", "-s", help="Force specific skill (bypasses routing)")
@click.option("--verbose", "-v", is_flag=True, help="Show routing and execution details")
def ask(prompt: str, skill: Optional[str], verbose: bool):
    """Ask AI with automatic skill routing

    Examples:
        pai ask "research quantum computing"
        pai ask "help me debug" --skill CORE
    """
    # Load config
    config = load_config()

    if not config["anthropic_api_key"]:
        click.echo("❌ Error: anthropic_api_key not set in config.yaml", err=True)
        click.echo("💡 Create ~/.config/pai/config.yaml with your API key", err=True)
        raise click.Abort()

    # Route to skill (or use forced skill)
    skill_name = skill if skill else route_to_skill(prompt)

    if verbose:
        click.echo(f"→ Routing to {skill_name} skill", err=True)

    # Execute with skill context
    try:
        response = execute_with_skill(prompt, skill_name, config)
        click.echo(response)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

    except Exception as e:
        click.echo(f"❌ API Error: {e}", err=True)
        raise click.Abort()


@cli.command()
def skills():
    """List all available skills"""
    if not SKILLS_DIR.exists():
        click.echo("❌ Skills directory not found", err=True)
        click.echo(f"💡 Create skills at: {SKILLS_DIR}", err=True)
        return

    skill_files = sorted(SKILLS_DIR.glob("*.md"))

    if not skill_files:
        click.echo("No skills found", err=True)
        return

    click.echo("Available skills:")
    for skill_file in skill_files:
        # Try to extract description from frontmatter
        content = skill_file.read_text()
        description = ""

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1])
                    description = meta.get("description", "").split("\n")[0]
                except yaml.YAMLError:
                    pass

        click.echo(f"  {skill_file.stem:15} {description}")


@cli.command()
@click.argument("skill_name")
def show(skill_name: str):
    """Show skill content

    Examples:
        pai show CORE
        pai show research
    """
    try:
        content = load_skill(skill_name)
        click.echo(content)

    except FileNotFoundError:
        click.echo(f"❌ Skill not found: {skill_name}", err=True)
        click.echo("\nAvailable skills:", err=True)
        for skill_file in SKILLS_DIR.glob("*.md"):
            click.echo(f"  - {skill_file.stem}", err=True)
        raise click.Abort()


@cli.command()
def init():
    """Initialize PAI directory structure"""
    directories = [
        SKILLS_DIR,
        AGENTS_DIR,
        PAI_DIR / "history" / "sessions",
        PAI_DIR / "history" / "learnings",
        PAI_DIR / "history" / "research",
        PAI_DIR / "history" / "raw-outputs",
        PAI_DIR / "plugins"
    ]

    click.echo("Initializing PAI directory structure...")

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        click.echo(f"  ✓ {directory}")

    # Create default config if it doesn't exist
    if not CONFIG_PATH.exists():
        default_config = {
            "anthropic_api_key": "your-api-key-here",
            "elevenlabs_api_key": "your-elevenlabs-key-here",
            "default_model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "voices": {
                "kai": "voice-id-kai",
                "researcher": "voice-id-researcher",
                "engineer": "voice-id-engineer"
            }
        }

        CONFIG_PATH.write_text(yaml.dump(default_config, default_flow_style=False))
        click.echo(f"  ✓ {CONFIG_PATH} (edit with your API keys)")

    # Create sample CORE skill
    core_path = SKILLS_DIR / "CORE.md"
    if not core_path.exists():
        core_content = """---
name: CORE
triggers:
  - "help"
  - "core"
  - "about"
---

# PAI CORE Context

## Identity
You are PAI - Personal AI Infrastructure, a minimal Python implementation
combining Unix philosophy, Karpathy code quality, and Simon Willison's design.

## Capabilities
- Skill-based routing
- Automatic history capture
- Agent delegation
- Voice feedback (optional)

## Response Format
Use structured output:
- 📋 SUMMARY: Brief overview
- ⚡ ACTIONS: Steps taken
- ✅ RESULTS: Outcomes
- 🎯 COMPLETED: [One-line completion for voice]

## Available Skills
Check with: pai skills
"""

        core_path.write_text(core_content)
        click.echo(f"  ✓ {core_path}")

    click.echo("\n✅ PAI initialized successfully!")
    click.echo("\nNext steps:")
    click.echo("  1. Edit config.yaml with your API keys")
    click.echo("  2. Try: pai ask 'help me get started'")


if __name__ == "__main__":
    cli()
