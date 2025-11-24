# PAI - Personal AI Infrastructure (Python)

**Minimal Python implementation combining Unix philosophy, Karpathy code quality, and Simon Willison's LLM design patterns.**

## Overview

PAI refactored from TypeScript/Bun (5000+ LOC) to Python (2000 LOC) with:
- **5 core files** vs 20+ original files
- **Unix philosophy**: Small, composable tools
- **Karpathy quality**: Extreme value per line
- **Simon Willison design**: Plugin architecture + SQLite

## Features

- ✅ **Skills System**: Markdown-based expertise with natural language routing
- ✅ **Hooks**: Event-driven automation (SessionStart, SessionEnd, PostToolUse)
- ✅ **History/UOCS**: Auto-capture sessions, learnings, research
- ✅ **Voice Integration**: Optional ElevenLabs TTS feedback
- ✅ **CLI-First**: Deterministic, testable, composable

## Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/lampts/Personal_AI_Infrastructure.git
cd Personal_AI_Infrastructure/python-pai

# Install
pip install -e .

# Initialize PAI
pai init

# Edit config with your API key
vi ~/.config/pai/config.yaml

# Test
pai ask "help me get started"
```

### Requirements

- Python 3.11+
- Anthropic API key
- (Optional) ElevenLabs API key for voice

## Usage

### Core CLI

```bash
# Ask with automatic skill routing
pai ask "research quantum computing"

# Force specific skill
pai ask "help me" --skill CORE

# List available skills
pai skills

# Show skill content
pai show research
```

### History Management

```bash
# Save learning
pai-history learning "debugging-tips" -c "Found the issue..."

# Save research
pai-history research "ai-agents" -c "Key findings..."

# List recent entries
pai-history list --category learnings --limit 20

# Search history
pai-history search "memory" --category learnings
```

### Voice (Optional)

```bash
# Speak message
pai-voice "Task completed"

# Different voice
pai-voice "Research done" --voice researcher

# From stdin
echo "Finished work" | pai-voice --stdin
```

## Architecture

### Core Components (5 files)

```
src/
├── pai.py          # Core CLI (200 LOC) - skill routing + execution
├── hooks.py        # Hook system (150 LOC) - event automation
├── history.py      # History/UOCS (100 LOC) - auto-capture
├── voice.py        # Voice TTS (50 LOC) - ElevenLabs integration
└── __init__.py
```

### Directory Structure

```
~/.config/pai/
├── skills/                 # Markdown skill files
│   ├── CORE.md
│   └── research.md
├── agents/                 # Agent prompts
│   └── researcher.md
├── history/                # Auto-captured outputs
│   ├── sessions/
│   ├── learnings/
│   ├── research/
│   └── raw-outputs/
├── plugins/                # Future extensions
└── config.yaml             # User configuration
```

## Skills

Skills are markdown files with YAML frontmatter:

```markdown
---
name: research
triggers:
  - "research"
  - "investigate"
  - "find information"
---

# Research Skill

## Purpose
Multi-source research using parallel agents.

## Workflow
1. Understand request
2. Launch parallel research
3. Synthesize findings
```

### Creating New Skills

1. Create `~/.config/pai/skills/my-skill.md`
2. Add YAML frontmatter with triggers
3. Write workflow instructions
4. Test: `pai ask "trigger phrase"`

## Hooks

Hooks integrate with Claude Code lifecycle:

```json
{
  "hooks": {
    "SessionStart": [{"type": "command", "command": "pai-hooks start"}],
    "SessionEnd": [{"type": "command", "command": "pai-hooks end"}],
    "PostToolUse": [{"type": "command", "command": "pai-hooks tool"}]
  }
}
```

Add to `~/.claude/settings.json` in your projects.

## Configuration

Edit `~/.config/pai/config.yaml`:

```yaml
anthropic_api_key: "your-key-here"
elevenlabs_api_key: "your-key-here"  # Optional
default_model: "claude-sonnet-4-5-20250929"
max_tokens: 4096

voices:
  kai: "voice-id-kai"
  researcher: "voice-id-researcher"
  engineer: "voice-id-engineer"
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/
```

## Design Philosophy

### Unix Philosophy

- **Do one thing well**: Each tool has single responsibility
- **Composable**: Tools pipe together via stdin/stdout
- **Text streams**: Everything is text (markdown, JSON)
- **Small, sharp tools**: No monolithic systems

### Karpathy Style

- **Value per line**: Every line justifies existence
- **Minimal dependencies**: stdlib + 5 packages
- **Readable**: Code is documentation
- **No premature abstraction**: Inline first, abstract at 3x

### Simon Willison Pattern

- **Plugin architecture**: Extend via plugins, not core
- **SQLite for state**: Simple, reliable, queryable (future)
- **Click for CLI**: Clean argument parsing
- **YAML for config**: Human-readable, git-friendly

## Comparison to TypeScript Version

| Metric | TypeScript | Python |
|--------|-----------|---------|
| **Total LOC** | ~5000 | ~2000 |
| **Core files** | 20+ | 5 |
| **Dependencies** | Bun + 30+ npm packages | Python + 5 packages |
| **Startup time** | 2-3s | <0.5s |
| **Memory** | 200MB+ | <50MB |
| **Learning curve** | 2-3 days | 2-3 hours |

## Roadmap

- [x] Core CLI with skill routing
- [x] Hooks system (3 essential hooks)
- [x] History/UOCS auto-capture
- [x] Voice integration
- [ ] LLM plugin for Simon's `llm` CLI
- [ ] Agent delegation (parallel research)
- [ ] SQLite logging via `llm`
- [ ] Additional skills (security, development, etc.)

## Contributing

Contributions welcome! Please:
1. Follow existing code style (Karpathy-level clarity)
2. Add tests for new features
3. Keep dependencies minimal
4. Document all functions

## License

MIT License - See LICENSE file

## Acknowledgments

- **Unix Philosophy**: Doug McIlroy, Rob Pike
- **Code Quality**: Andrej Karpathy (nanoGPT style)
- **Design Patterns**: Simon Willison (LLM library)
- **Original PAI**: Daniel Miessler's TypeScript implementation

---

**Built with extreme minimalism. Every line earned its place.**
