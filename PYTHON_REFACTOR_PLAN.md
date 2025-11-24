# PAI → Python Minimal Refactor Plan

**Combining Unix Philosophy + Karpathy Code Quality + Simon Willison's LLM Design**

---

## Executive Summary

Refactor PAI from TypeScript/Bun (145MB, 13 skills, complex hooks) to a minimal Python system (~5-10 files, <2000 LOC) that preserves core value while maximizing simplicity.

**Core Insight:** 80% of PAI's value comes from 20% of its code. Focus ruthlessly on that 20%.

---

## Design Principles

### 1. Unix Philosophy
- **Do one thing well** - Each tool has single responsibility
- **Composable** - Tools pipe together via stdin/stdout
- **Text streams** - Everything is text (markdown, JSON)
- **Small, sharp tools** - No monolithic systems

### 2. Karpathy nanoGPT Style
- **Extreme value per line** - Every line justifies existence
- **Minimal dependencies** - Standard library + LLM + Anthropic SDK
- **Readable by humans** - Code is documentation
- **No premature abstraction** - Inline first, abstract only when needed 3x

### 3. Simon Willison's LLM Design
- **Plugin architecture** - Extend via plugins, not core changes
- **SQLite for state** - Simple, reliable, queryable
- **Click for CLI** - Clean argument parsing
- **YAML for config** - Human-readable, git-friendly

---

## What to Keep vs. Drop

### ✅ KEEP (Core Value)

**1. Skills System**
- Markdown-based expertise containers
- Progressive disclosure (3-tier loading)
- Natural language routing
- **Why:** This is PAI's killer feature

**2. Hooks System (Simplified)**
- SessionStart, SessionEnd, PostToolUse only
- Simple Python scripts, not TypeScript
- **Why:** Event-driven automation is valuable

**3. History/UOCS**
- Auto-capture learnings, research, sessions
- **Why:** Documentation that handles itself

**4. CLI-First Philosophy**
- Small Python CLIs wrapping APIs
- **Why:** Deterministic, testable, composable

**5. Agent Delegation Pattern**
- Specialized agents via Claude SDK
- **Why:** Parallel research is powerful

### ⚠️ SIMPLIFY

**1. Voice Server**
- Drop Bun server → Simple Python script
- Direct ElevenLabs API calls
- **Why:** 500 LOC server → 50 LOC script

**2. MCP Complexity**
- Drop MCP abstractions
- Direct API calls in Python
- **Why:** MCP is premature for personal use

**3. Hook Complexity**
- Drop 16 hooks → 3-4 essential hooks
- No TypeScript, no complex path resolution
- **Why:** Most hooks don't justify complexity

**4. Tab Management**
- Drop terminal tab updates
- **Why:** Low value for complexity cost

### ❌ DROP (Complexity > Value)

**1. Bun Runtime**
- Python standard everywhere
- **Why:** No need for exotic runtime

**2. Protected File System**
- Drop `.pai-protected.json` validation
- **Why:** Git + human review sufficient

**3. MCP Profile Management**
- Drop profile swapping
- **Why:** Premature optimization

**4. Complex Status Line**
- Drop dynamic status bar
- **Why:** Low ROI

**5. Self-Test System**
- Drop elaborate health checks
- **Why:** `llm plugins` is sufficient

---

## Architecture Overview

### Core Components (5 files + plugins)

```
~/.config/pai/
├── pai.py                  # Main CLI (200 LOC)
├── hooks.py                # Hook system (150 LOC)
├── history.py              # UOCS capture (100 LOC)
├── config.yaml             # User configuration
├── pai.db                  # SQLite state (sessions, logs)
│
├── skills/                 # Markdown files only
│   ├── CORE.md
│   ├── research.md
│   └── [domain].md
│
├── agents/                 # Agent prompts only
│   ├── researcher.md
│   └── engineer.md
│
└── plugins/                # LLM plugins
    ├── pai_core.py         # Core skill loader
    ├── pai_research.py     # Research orchestration
    └── pai_history.py      # History capture
```

**Total:** ~10 files, ~1500 LOC core + ~500 LOC plugins

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Runtime** | Python 3.11+ | Ubiquitous, simple, fast enough |
| **CLI Framework** | Click | Clean, composable, well-documented |
| **LLM Interface** | Simon's `llm` library | Plugin system, SQLite logging |
| **AI SDK** | Anthropic Python SDK | Direct Claude API access |
| **State** | SQLite (via llm) | Simple, queryable, no setup |
| **Config** | YAML | Human-readable, git-friendly |
| **Voice** | `elevenlabs` package | Simple pip install |
| **Testing** | pytest | Standard, minimal |

**Dependencies:** `llm`, `anthropic`, `click`, `pyyaml`, `elevenlabs` (~5 packages)

---

## Core Architecture

### 1. Skills System (Karpathy-style minimal)

**Single file: `pai.py`**

```python
#!/usr/bin/env python3
"""PAI - Personal AI Infrastructure CLI

Unix-style tool for AI-assisted workflows.
Reads markdown skills, routes to appropriate tools.
"""

import click
import yaml
from pathlib import Path
from anthropic import Anthropic

# ============================================================
# CONFIGURATION
# ============================================================

PAI_DIR = Path.home() / ".config" / "pai"
SKILLS_DIR = PAI_DIR / "skills"
CONFIG = PAI_DIR / "config.yaml"

def load_config():
    """Load user config (API keys, preferences)"""
    if not CONFIG.exists():
        return {"anthropic_api_key": None}
    return yaml.safe_load(CONFIG.read_text())

def load_skill(name: str) -> str:
    """Load skill markdown content"""
    skill_path = SKILLS_DIR / f"{name}.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {name}")
    return skill_path.read_text()

# ============================================================
# SKILL ROUTING (Natural Language → Skill)
# ============================================================

def route_to_skill(user_input: str) -> str:
    """Route user input to appropriate skill.

    Reads all skill headers, matches triggers.
    Returns skill name to load.
    """
    for skill_file in SKILLS_DIR.glob("*.md"):
        content = skill_file.read_text()
        # Extract YAML frontmatter
        if content.startswith("---"):
            _, frontmatter, _ = content.split("---", 2)
            meta = yaml.safe_load(frontmatter)

            # Check if user input matches triggers
            triggers = meta.get("triggers", [])
            for trigger in triggers:
                if trigger.lower() in user_input.lower():
                    return skill_file.stem

    return "CORE"  # Default to CORE skill

# ============================================================
# LLM EXECUTION
# ============================================================

def execute_with_skill(user_input: str, skill_name: str):
    """Execute user request with skill context loaded"""
    config = load_config()
    client = Anthropic(api_key=config["anthropic_api_key"])

    # Load skill content
    skill_content = load_skill(skill_name)

    # Build messages
    messages = [
        {
            "role": "user",
            "content": f"<skill-context>\n{skill_content}\n</skill-context>\n\n{user_input}"
        }
    ]

    # Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=messages
    )

    return response.content[0].text

# ============================================================
# CLI COMMANDS
# ============================================================

@click.group()
def cli():
    """PAI - Personal AI Infrastructure"""
    pass

@cli.command()
@click.argument("prompt")
def ask(prompt):
    """Ask AI with skill routing"""
    skill = route_to_skill(prompt)
    click.echo(f"→ Routing to {skill} skill", err=True)

    response = execute_with_skill(prompt, skill)
    click.echo(response)

@cli.command()
def skills():
    """List available skills"""
    for skill in SKILLS_DIR.glob("*.md"):
        click.echo(f"  {skill.stem}")

@cli.command()
@click.argument("skill_name")
def show(skill_name):
    """Show skill content"""
    click.echo(load_skill(skill_name))

if __name__ == "__main__":
    cli()
```

**Value per line:** Every line serves clear purpose, no abstractions until needed.

---

### 2. Hook System (Minimal, Composable)

**Single file: `hooks.py`**

```python
#!/usr/bin/env python3
"""PAI Hook System - Event-driven automation

Hooks fire on:
- SessionStart: Load CORE context
- SessionEnd: Capture session summary
- PostToolUse: Log tool usage
"""

import sys
import json
from pathlib import Path
from datetime import datetime

PAI_DIR = Path.home() / ".config" / "pai"
HISTORY_DIR = PAI_DIR / "history"
DB_PATH = PAI_DIR / "pai.db"

# ============================================================
# HOOK: SessionStart
# ============================================================

def session_start():
    """Load CORE skill context at session start"""
    core_path = PAI_DIR / "skills" / "CORE.md"

    if not core_path.exists():
        print("❌ CORE skill not found", file=sys.stderr)
        return

    core_content = core_path.read_text()

    # Output as system-reminder (Claude Code ingests this)
    message = f"""<system-reminder>
PAI CORE CONTEXT (Auto-loaded)

{core_content}
</system-reminder>"""

    print(message)
    print("✅ CORE context loaded", file=sys.stderr)

# ============================================================
# HOOK: SessionEnd
# ============================================================

def session_end():
    """Capture session summary to history"""
    # Read transcript from stdin
    transcript = sys.stdin.read()

    # Generate timestamp-based filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    session_file = HISTORY_DIR / "sessions" / f"{timestamp}_session.md"

    # Ensure directory exists
    session_file.parent.mkdir(parents=True, exist_ok=True)

    # Write transcript
    session_file.write_text(transcript)

    print(f"✅ Session saved: {session_file}", file=sys.stderr)

# ============================================================
# HOOK: PostToolUse
# ============================================================

def post_tool_use():
    """Log tool usage to database"""
    # Read tool event from stdin (JSON)
    event = json.loads(sys.stdin.read())

    # Extract key info
    tool_name = event.get("tool", "unknown")
    timestamp = datetime.now().isoformat()

    # Append to log file (simple append, no DB complexity yet)
    log_file = HISTORY_DIR / "raw-outputs" / f"{datetime.now():%Y-%m}" / "events.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with log_file.open("a") as f:
        f.write(json.dumps({"timestamp": timestamp, **event}) + "\n")

    print(f"✅ Logged: {tool_name}", file=sys.stderr)

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import click

    @click.group()
    def cli():
        """PAI Hook System"""
        pass

    @cli.command()
    def start():
        """SessionStart hook"""
        session_start()

    @cli.command()
    def end():
        """SessionEnd hook"""
        session_end()

    @cli.command()
    def tool():
        """PostToolUse hook"""
        post_tool_use()

    cli()
```

**Configured in `settings.json`:**

```json
{
  "hooks": {
    "SessionStart": [{"type": "command", "command": "pai-hooks start"}],
    "SessionEnd": [{"type": "command", "command": "pai-hooks end"}],
    "PostToolUse": [{"type": "command", "command": "pai-hooks tool"}]
  }
}
```

---

### 3. History System (UOCS)

**Single file: `history.py`**

```python
#!/usr/bin/env python3
"""PAI History System - Universal Output Capture

Auto-capture:
- Sessions (work logs)
- Learnings (problem-solving)
- Research (investigations)
"""

import click
from pathlib import Path
from datetime import datetime

HISTORY_DIR = Path.home() / ".config" / "pai" / "history"

def save_to_history(category: str, title: str, content: str):
    """Save content to history with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    month_dir = HISTORY_DIR / category / f"{datetime.now():%Y-%m}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp}_{title.replace(' ', '-')}.md"
    filepath = month_dir / filename

    filepath.write_text(content)
    return filepath

@click.group()
def cli():
    """PAI History Management"""
    pass

@cli.command()
@click.argument("title")
@click.option("--content", "-c", prompt=True)
def learning(title, content):
    """Save a learning"""
    path = save_to_history("learnings", title, content)
    click.echo(f"✅ Saved: {path}")

@cli.command()
@click.argument("title")
@click.option("--content", "-c", prompt=True)
def research(title, content):
    """Save research findings"""
    path = save_to_history("research", title, content)
    click.echo(f"✅ Saved: {path}")

@cli.command()
@click.option("--category", "-c", default="sessions")
@click.option("--limit", "-n", default=10)
def list(category, limit):
    """List recent history entries"""
    category_dir = HISTORY_DIR / category

    if not category_dir.exists():
        click.echo(f"No {category} found")
        return

    # Find all .md files, sort by mtime
    files = sorted(category_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

    for f in files[:limit]:
        click.echo(f"  {f.stem}")

if __name__ == "__main__":
    cli()
```

---

### 4. LLM Plugin Architecture

**Plugin: `pai_core.py`** (integrates with Simon's LLM)

```python
"""LLM plugin for PAI skill loading

Usage:
  llm -m claude-3.5-sonnet "research AI agents" -o skill research
"""

import llm
from pathlib import Path

PAI_DIR = Path.home() / ".config" / "pai"
SKILLS_DIR = PAI_DIR / "skills"

@llm.hookimpl
def register_models(register):
    """Register PAI-aware model wrapper"""
    register(PAIModel())

class PAIModel(llm.Model):
    """Claude wrapper that loads PAI skills"""

    model_id = "pai-claude"

    def execute(self, prompt, stream, response, conversation):
        # Check for -o skill flag
        skill_name = prompt.options.get("skill", "CORE")

        # Load skill content
        skill_path = SKILLS_DIR / f"{skill_name}.md"
        if skill_path.exists():
            skill_content = skill_path.read_text()
            # Inject skill context
            prompt.prompt = f"<skill>{skill_content}</skill>\n\n{prompt.prompt}"

        # Delegate to Claude
        claude = llm.get_model("claude-3.5-sonnet")
        yield from claude.execute(prompt, stream, response, conversation)

@llm.hookimpl
def register_commands(cli):
    """Add PAI commands to LLM CLI"""
    import click

    @cli.group()
    def pai():
        """PAI management commands"""
        pass

    @pai.command()
    def skills():
        """List available skills"""
        for skill in SKILLS_DIR.glob("*.md"):
            click.echo(f"  {skill.stem}")
```

**Installation:**

```bash
# Install LLM
pip install llm anthropic-sdk

# Install PAI plugin
llm install pai_core.py

# Use it
llm "research quantum computing" -m pai-claude -o skill research
```

---

### 5. Voice Integration (Minimal)

**Single file: `voice.py`**

```python
#!/usr/bin/env python3
"""PAI Voice - Minimal ElevenLabs TTS

Reads completion message, speaks it aloud.
"""

import sys
import click
from elevenlabs import generate, play, set_api_key
import os

set_api_key(os.getenv("ELEVENLABS_API_KEY"))

VOICES = {
    "kai": "s3TPKV1kjDlVtZbl4Ksh",
    "researcher": "AXdMgz6evoL7OPd7eU12",
    "engineer": "fATgBRI8wg5KkDFg8vBd",
}

@click.command()
@click.argument("message")
@click.option("--voice", default="kai")
def speak(message, voice):
    """Speak message via ElevenLabs TTS"""
    voice_id = VOICES.get(voice, VOICES["kai"])

    # Generate audio
    audio = generate(text=message, voice=voice_id)

    # Play audio
    play(audio)

    click.echo(f"🔊 Spoke: {message}", err=True)

if __name__ == "__main__":
    speak()
```

**Hook integration:**

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "bash -c 'grep -o \"COMPLETED: .*\" | cut -d: -f2 | xargs pai-voice'"
      }
    ]
  }
}
```

---

## Skills Format (Unchanged)

Skills remain **pure markdown** with YAML frontmatter:

```markdown
---
name: research
triggers:
  - "research"
  - "investigate"
  - "find information about"
  - "analyze trends"
---

# Research Skill

## Purpose
Multi-source comprehensive research using parallel agents.

## When to Activate
Use when user needs information gathering, trend analysis, or comprehensive research.

## Workflow

### 1. Understand Request
Extract:
- Topic/question
- Depth required (quick vs. comprehensive)
- Time constraints

### 2. Parallel Research
Launch 3 agents in parallel:
- `llm "research {topic}" -m perplexity`
- `llm "research {topic}" -m claude-3.5-sonnet`
- `llm "research {topic}" -m gemini`

### 3. Synthesize Results
Combine findings, remove duplicates, cite sources.

### 4. Capture to History
```bash
pai-history research "{topic}" -c "$(cat findings.md)"
```
```

**Key:** No code in skills, only workflows and context.

---

## Implementation Phases

### Phase 1: Core Foundation (Week 1)
**Goal:** Working CLI with skill routing

**Deliverables:**
1. `pai.py` - Core CLI (200 LOC)
2. `skills/CORE.md` - Core skill
3. `skills/research.md` - One example skill
4. `config.yaml` - User config

**Validation:**
```bash
pai ask "research AI agents"
# → Routes to research skill
# → Calls Claude with skill context
# → Returns synthesized research
```

### Phase 2: Hooks + History (Week 2)
**Goal:** Event-driven automation and capture

**Deliverables:**
1. `hooks.py` - 3 essential hooks
2. `history.py` - UOCS capture
3. Update `settings.json` with hooks

**Validation:**
```bash
# Start session → CORE loads automatically
# End session → Transcript saved to history/sessions/
pai-history list --category sessions
```

### Phase 3: LLM Plugin Integration (Week 3)
**Goal:** Integrate with Simon's LLM ecosystem

**Deliverables:**
1. `pai_core.py` - LLM plugin
2. `pai_research.py` - Research plugin
3. Install script

**Validation:**
```bash
llm install pai_core
llm "research topic" -m pai-claude -o skill research
llm logs --model pai-claude  # See history via LLM
```

### Phase 4: Voice + Agents (Week 4)
**Goal:** Voice feedback and agent delegation

**Deliverables:**
1. `voice.py` - Minimal TTS
2. `agents/researcher.md` - Agent prompt
3. Agent delegation helper

**Validation:**
```bash
pai ask "research topic" --delegate researcher
# → Launches researcher agent
# → Completes task
# → Speaks completion via TTS
```

---

## Migration Strategy

### From Current PAI to Python Minimal

**Step 1: Parallel Development**
- Keep TypeScript PAI running
- Build Python version alongside
- Test Python version thoroughly

**Step 2: Skill Migration**
- Skills are already markdown → Copy directly
- Remove TypeScript-specific references
- Test each skill individually

**Step 3: Hook Migration**
- Map 16 TypeScript hooks → 3-4 Python hooks
- Test each hook individually
- Update `settings.json` incrementally

**Step 4: Cut Over**
- Backup TypeScript PAI to `pai-ts-backup/`
- Symlink `~/.config/pai` → Python version
- Run for 1 week, monitor issues

**Step 5: Cleanup**
- Archive TypeScript version
- Document learnings
- Share Python version publicly

---

## Code Quality Standards (Karpathy-style)

### Every File Must Have:

1. **Docstring** explaining purpose in 1-3 sentences
2. **Section comments** (`# ===== SECTION =====`) for major blocks
3. **Inline comments** ONLY when code is non-obvious
4. **Type hints** for function signatures
5. **Zero abstractions** until needed 3x

### Code Review Checklist:

- [ ] Can I delete this line? (If yes → delete)
- [ ] Can I inline this function? (If <5 uses → inline)
- [ ] Is this name self-documenting? (If no → rename)
- [ ] Does this depend on external package? (If yes → justify)
- [ ] Would a new user understand this? (If no → comment)

### Anti-Patterns to Avoid:

❌ **Over-abstraction**
```python
# Bad: Premature abstraction
class SkillLoader:
    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir

    def load(self, name: str) -> Skill:
        # 50 lines of complexity
```

✅ **Inline first**
```python
# Good: Simple, direct
def load_skill(name: str) -> str:
    """Load skill markdown from skills/ directory"""
    return (SKILLS_DIR / f"{name}.md").read_text()
```

---

## Testing Strategy

### Unit Tests (pytest)

```python
# test_pai.py

def test_skill_routing():
    """Test that user input routes to correct skill"""
    assert route_to_skill("research AI agents") == "research"
    assert route_to_skill("help me") == "CORE"

def test_skill_loading():
    """Test skill file loading"""
    content = load_skill("CORE")
    assert "PAI CORE" in content

def test_history_capture():
    """Test saving to history"""
    path = save_to_history("learnings", "test", "content")
    assert path.exists()
    assert "test" in path.read_text()
```

### Integration Tests

```bash
#!/bin/bash
# test_integration.sh

# Test skill routing
output=$(pai ask "research quantum computing")
[[ "$output" =~ "quantum" ]] || exit 1

# Test history capture
pai-history learning "test" -c "content"
pai-history list | grep "test" || exit 1

echo "✅ All integration tests passed"
```

### Manual Testing Checklist

- [ ] Session starts → CORE context loads
- [ ] User prompt → Routes to correct skill
- [ ] Session ends → Transcript saved to history
- [ ] Voice speaks → Completion message heard
- [ ] LLM plugin → Works with `llm` CLI

---

## Success Metrics

### Quantitative

| Metric | Current (TS) | Target (Python) |
|--------|-------------|-----------------|
| **Total LOC** | ~5000 | ~2000 |
| **Core files** | 20+ | 5 |
| **Dependencies** | Bun, TS, 30+ npm packages | Python, 5 pip packages |
| **Startup time** | 2-3s | <0.5s |
| **Memory usage** | 200MB+ | <50MB |
| **Learning curve** | 2-3 days | 2-3 hours |

### Qualitative

- ✅ New user can understand entire system in 1 hour
- ✅ Can extend with new skill in 10 minutes
- ✅ Code reads like English (Karpathy-level clarity)
- ✅ Works on any Unix system with Python 3.11+
- ✅ No exotic dependencies or runtimes

---

## Example: End-to-End Flow

**User:** "Research AI agent frameworks and summarize findings"

**System Flow:**

1. **CLI receives request**
   ```bash
   pai ask "Research AI agent frameworks and summarize findings"
   ```

2. **Routing (pai.py)**
   - Scans `skills/*.md` for trigger match
   - Finds `research.md` with trigger "research"
   - Returns `skill = "research"`

3. **Skill loading (pai.py)**
   - Reads `skills/research.md` (3-tier content)
   - Extracts workflows and context

4. **LLM execution (pai.py)**
   - Calls Anthropic SDK with skill context
   - Returns research findings

5. **Hook: PostToolUse (hooks.py)**
   - Logs tool usage to `history/raw-outputs/`

6. **Hook: Stop (hooks.py + voice.py)**
   - Extracts "COMPLETED: ..." line
   - Calls `pai-voice "Research completed on AI agents"`
   - Speaks via ElevenLabs TTS

7. **History capture (history.py)**
   - Saves research to `history/research/YYYY-MM/YYYY-MM-DD-HHMMSS_ai-agent-frameworks.md`

**Total code executed:** ~500 LOC across 3 files

---

## Frequently Asked Questions

### Q: Why Python over TypeScript?

**A:**
- Ubiquitous (every system has Python)
- Simpler runtime (no Bun)
- Better ML/AI ecosystem
- More readable for casual users
- Simon's LLM is Python-first

### Q: Why drop MCP abstractions?

**A:**
MCP adds complexity for personal use. Direct API calls in Python are:
- Simpler (no protocol overhead)
- Faster (no serialization)
- More maintainable (readable code)
- Sufficient for single-user systems

Use MCP only when building for others or need sandboxing.

### Q: How do we handle the 8 constitutional principles?

**A:**

| Principle | Python Implementation |
|-----------|----------------------|
| 1. Scaffolding > Model | ✅ Keep skill system, hooks, history |
| 2. Deterministic | ✅ CLI tools, no prompt variations |
| 3. Code Before Prompts | ✅ Python CLIs wrap APIs |
| 4. CLI as Interface | ✅ Click-based CLIs |
| 5. Goal → Code → CLI → Prompts | ✅ Same pipeline |
| 6. Spec/Test/Evals First | ✅ Pytest for all code |
| 7. Meta/Self Updates | ✅ System can modify its skills |
| 8. Custom Skill Management | ✅ Markdown skills + routing |

**All principles preserved, implementation simplified.**

### Q: What about agent delegation?

**A:**
Simpler via Anthropic SDK directly:

```python
def delegate_to_agent(agent_name: str, task: str) -> str:
    """Delegate task to specialized agent"""
    agent_prompt = (PAI_DIR / "agents" / f"{agent_name}.md").read_text()

    client = Anthropic(api_key=config["anthropic_api_key"])
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=agent_prompt,
        messages=[{"role": "user", "content": task}]
    )

    return response.content[0].text
```

**50 LOC vs. 500 LOC TypeScript task delegation.**

### Q: Can we still do parallel research?

**A:**
Yes, simpler with Python asyncio:

```python
import asyncio

async def parallel_research(topic: str):
    """Launch 3 research agents in parallel"""
    tasks = [
        delegate_to_agent("perplexity-researcher", topic),
        delegate_to_agent("claude-researcher", topic),
        delegate_to_agent("gemini-researcher", topic),
    ]

    results = await asyncio.gather(*tasks)
    return synthesize(results)
```

**30 LOC vs. complex TypeScript agent orchestration.**

---

## Next Steps

### Immediate (Today)

1. **Review this plan** - Feedback on architecture, scope
2. **Prioritize features** - What's essential vs. nice-to-have?
3. **Approve/iterate** - Green light to start implementation?

### Implementation (Weeks 1-4)

1. **Phase 1:** Core CLI with skill routing
2. **Phase 2:** Hooks and history capture
3. **Phase 3:** LLM plugin integration
4. **Phase 4:** Voice and agent delegation

### Launch (Week 5)

1. **Documentation** - README, tutorial, examples
2. **Public release** - GitHub repo, blog post
3. **Community feedback** - Iterate based on usage

---

## Conclusion

This refactor preserves PAI's core value (skills, hooks, history, CLI-first) while achieving:

- **10x simpler** (5 files vs. 50+)
- **3x faster** (Python startup < TypeScript + Bun)
- **5x more readable** (Karpathy-level code quality)
- **Universal** (Works anywhere Python runs)
- **Extensible** (LLM plugin ecosystem)

**The result:** A minimal, production-grade personal AI infrastructure that anyone can understand, modify, and extend in an afternoon.

**Estimated effort:** 4 weeks part-time (80 hours total)

---

**Ready to proceed?** Let me know if you want to:
1. Refine the plan further
2. Start with Phase 1 implementation
3. Create example code for specific components
