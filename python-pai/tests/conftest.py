"""Pytest configuration and shared fixtures for PAI tests

Provides:
- Temporary PAI directory setup
- Mock API responses
- Sample skills and configurations
"""

import pytest
from pathlib import Path
from typing import Generator
import yaml


@pytest.fixture
def temp_pai_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary PAI directory structure with sample files

    Returns:
        Path to temporary ~/.config/pai directory
    """
    pai_dir = tmp_path / ".config" / "pai"

    # Create directory structure
    (pai_dir / "skills").mkdir(parents=True)
    (pai_dir / "agents").mkdir(parents=True)
    (pai_dir / "history" / "sessions").mkdir(parents=True)
    (pai_dir / "history" / "learnings").mkdir(parents=True)
    (pai_dir / "history" / "research").mkdir(parents=True)
    (pai_dir / "history" / "raw-outputs").mkdir(parents=True)
    (pai_dir / "plugins").mkdir(parents=True)

    yield pai_dir

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def sample_core_skill(temp_pai_dir: Path) -> Path:
    """Create sample CORE skill file

    Returns:
        Path to CORE.md skill file
    """
    core_content = """---
name: CORE
triggers:
  - "help"
  - "core"
  - "about"
---

# PAI CORE Context

## Identity
You are PAI - Personal AI Infrastructure.

## Capabilities
- Skill routing
- History capture
- Agent delegation

## Response Format
Always use structured output:
- 📋 SUMMARY: Brief overview
- ⚡ ACTIONS: Steps taken
- ✅ RESULTS: Outcomes
"""

    core_path = temp_pai_dir / "skills" / "CORE.md"
    core_path.write_text(core_content)
    return core_path


@pytest.fixture
def sample_research_skill(temp_pai_dir: Path) -> Path:
    """Create sample research skill file

    Returns:
        Path to research.md skill file
    """
    research_content = """---
name: research
triggers:
  - "research"
  - "investigate"
  - "find information"
  - "analyze trends"
---

# Research Skill

## Purpose
Multi-source comprehensive research using parallel agents.

## Workflow

### 1. Understand Request
Extract topic, depth, and constraints.

### 2. Parallel Research
Launch multiple agents in parallel.

### 3. Synthesize Results
Combine findings and cite sources.
"""

    research_path = temp_pai_dir / "skills" / "research.md"
    research_path.write_text(research_content)
    return research_path


@pytest.fixture
def sample_config(temp_pai_dir: Path) -> Path:
    """Create sample configuration file

    Returns:
        Path to config.yaml
    """
    config_data = {
        "anthropic_api_key": "test-key-12345",
        "elevenlabs_api_key": "test-elevenlabs-key",
        "default_model": "claude-sonnet-4-5-20250929",
        "voices": {
            "kai": "voice-id-kai",
            "researcher": "voice-id-researcher",
            "engineer": "voice-id-engineer"
        }
    }

    config_path = temp_pai_dir / "config.yaml"
    config_path.write_text(yaml.dump(config_data))
    return config_path


@pytest.fixture
def sample_agent(temp_pai_dir: Path) -> Path:
    """Create sample agent prompt file

    Returns:
        Path to researcher.md agent file
    """
    agent_content = """---
name: researcher
voice_id: voice-id-researcher
---

# Researcher Agent

## Role
Information gathering and research specialist.

## Capabilities
- Web research via multiple sources
- Fact verification
- Citation tracking
- Trend analysis

## Instructions
1. Always cite sources
2. Cross-reference multiple sources
3. Provide confidence levels
4. Flag contradictory information
"""

    agent_path = temp_pai_dir / "agents" / "researcher.md"
    agent_path.write_text(agent_content)
    return agent_path


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response

    Returns:
        Mock response object with expected structure
    """
    class MockContent:
        def __init__(self, text: str):
            self.text = text

    class MockResponse:
        def __init__(self, text: str):
            self.content = [MockContent(text)]

    return MockResponse


@pytest.fixture
def mock_elevenlabs_audio():
    """Mock ElevenLabs audio response

    Returns:
        Mock audio bytes
    """
    return b"mock-audio-data"


@pytest.fixture
def sample_session_transcript() -> str:
    """Sample session transcript for testing

    Returns:
        Multi-line session transcript
    """
    return """User: Research quantum computing trends

AI: 📋 SUMMARY: Quantum computing research complete
⚡ ACTIONS: Analyzed 15 sources across academic and industry publications
✅ RESULTS: Comprehensive trends analysis with key findings
🎯 COMPLETED: Research on quantum computing trends finished
"""


@pytest.fixture
def monkeypatch_pai_dir(monkeypatch, temp_pai_dir: Path):
    """Monkeypatch PAI_DIR to use temp directory

    Args:
        monkeypatch: pytest monkeypatch fixture
        temp_pai_dir: Temporary PAI directory
    """
    monkeypatch.setenv("PAI_DIR", str(temp_pai_dir))
    return temp_pai_dir
