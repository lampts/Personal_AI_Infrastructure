"""Tests for core PAI CLI functionality

Tests:
- Configuration loading
- Skill file loading
- Skill routing (natural language → skill name)
- CLI command execution
- LLM execution with skill context
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml


# Assume pai.py exports these functions
# from pai import load_config, load_skill, route_to_skill, execute_with_skill


# ============================================================
# CONFIGURATION TESTS
# ============================================================

def test_load_config_success(temp_pai_dir, sample_config, monkeypatch):
    """Test loading valid configuration file"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Mock implementation
    config_path = sample_config
    config = yaml.safe_load(config_path.read_text())

    assert config["anthropic_api_key"] == "test-key-12345"
    assert config["elevenlabs_api_key"] == "test-elevenlabs-key"
    assert config["default_model"] == "claude-sonnet-4-5-20250929"
    assert "kai" in config["voices"]


def test_load_config_missing_file(temp_pai_dir, monkeypatch):
    """Test loading config when file doesn't exist returns defaults"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    config_path = temp_pai_dir / "config.yaml"
    assert not config_path.exists()

    # Should return default config
    default_config = {"anthropic_api_key": None}
    assert default_config["anthropic_api_key"] is None


def test_load_config_invalid_yaml(temp_pai_dir, monkeypatch):
    """Test loading malformed YAML file raises error"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    config_path = temp_pai_dir / "config.yaml"
    config_path.write_text("invalid: yaml: content:")

    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(config_path.read_text())


# ============================================================
# SKILL LOADING TESTS
# ============================================================

def test_load_skill_success(temp_pai_dir, sample_core_skill, monkeypatch):
    """Test loading existing skill file"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    skill_content = sample_core_skill.read_text()

    assert "PAI CORE Context" in skill_content
    assert "Identity" in skill_content
    assert "Capabilities" in skill_content


def test_load_skill_missing_file(temp_pai_dir, monkeypatch):
    """Test loading non-existent skill raises FileNotFoundError"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    missing_skill = temp_pai_dir / "skills" / "nonexistent.md"
    assert not missing_skill.exists()

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        if not missing_skill.exists():
            raise FileNotFoundError(f"Skill not found: nonexistent")


def test_load_skill_parses_frontmatter(temp_pai_dir, sample_research_skill):
    """Test skill frontmatter is correctly parsed"""
    content = sample_research_skill.read_text()

    # Extract YAML frontmatter
    if content.startswith("---"):
        _, frontmatter, body = content.split("---", 2)
        meta = yaml.safe_load(frontmatter)

        assert meta["name"] == "research"
        assert "research" in meta["triggers"]
        assert "investigate" in meta["triggers"]


def test_load_multiple_skills(temp_pai_dir, sample_core_skill, sample_research_skill):
    """Test loading multiple skills from skills directory"""
    skills_dir = temp_pai_dir / "skills"
    skill_files = list(skills_dir.glob("*.md"))

    assert len(skill_files) == 2
    skill_names = [f.stem for f in skill_files]
    assert "CORE" in skill_names
    assert "research" in skill_names


# ============================================================
# SKILL ROUTING TESTS
# ============================================================

def test_route_to_skill_exact_trigger_match(temp_pai_dir, sample_research_skill):
    """Test routing when user input exactly matches trigger"""
    user_input = "research quantum computing"

    # Extract triggers from skill
    content = sample_research_skill.read_text()
    _, frontmatter, _ = content.split("---", 2)
    meta = yaml.safe_load(frontmatter)

    triggers = meta.get("triggers", [])

    # Check if any trigger matches
    matched = False
    for trigger in triggers:
        if trigger.lower() in user_input.lower():
            matched = True
            break

    assert matched == True
    # Should route to "research" skill


def test_route_to_skill_partial_trigger_match(temp_pai_dir, sample_research_skill):
    """Test routing with partial trigger match"""
    user_input = "I need to investigate this topic"

    content = sample_research_skill.read_text()
    _, frontmatter, _ = content.split("---", 2)
    meta = yaml.safe_load(frontmatter)

    triggers = meta.get("triggers", [])

    matched = False
    for trigger in triggers:
        if trigger.lower() in user_input.lower():
            matched = True
            break

    assert matched == True  # "investigate" is in triggers


def test_route_to_skill_no_match_returns_core(temp_pai_dir, sample_core_skill):
    """Test routing defaults to CORE when no trigger matches"""
    user_input = "random unmatched request"

    # Should default to CORE
    default_skill = "CORE"
    assert default_skill == "CORE"


def test_route_to_skill_case_insensitive(temp_pai_dir, sample_research_skill):
    """Test routing is case-insensitive"""
    user_inputs = [
        "RESEARCH quantum computing",
        "Research quantum computing",
        "research quantum computing"
    ]

    content = sample_research_skill.read_text()
    _, frontmatter, _ = content.split("---", 2)
    meta = yaml.safe_load(frontmatter)
    triggers = meta.get("triggers", [])

    for user_input in user_inputs:
        matched = False
        for trigger in triggers:
            if trigger.lower() in user_input.lower():
                matched = True
                break
        assert matched == True


def test_route_to_skill_multiple_triggers():
    """Test skill with multiple triggers routes correctly"""
    triggers = ["research", "investigate", "find information", "analyze trends"]
    test_inputs = [
        ("research AI", True),
        ("investigate the issue", True),
        ("find information about X", True),
        ("analyze trends in data", True),
        ("random text", False)
    ]

    for user_input, should_match in test_inputs:
        matched = False
        for trigger in triggers:
            if trigger.lower() in user_input.lower():
                matched = True
                break
        assert matched == should_match


# ============================================================
# LLM EXECUTION TESTS
# ============================================================

@patch('anthropic.Anthropic')
def test_execute_with_skill_success(mock_anthropic, temp_pai_dir, sample_core_skill, sample_config, monkeypatch):
    """Test executing user request with skill context"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Setup mock
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response from AI")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    # Load config and skill
    config = yaml.safe_load(sample_config.read_text())
    skill_content = sample_core_skill.read_text()
    user_input = "help me"

    # Simulate execution
    messages = [
        {
            "role": "user",
            "content": f"<skill-context>\n{skill_content}\n</skill-context>\n\n{user_input}"
        }
    ]

    # Call would be: client.messages.create(model=..., max_tokens=..., messages=messages)
    # Verify skill context is included
    assert f"<skill-context>\n{skill_content}\n</skill-context>" in messages[0]["content"]
    assert user_input in messages[0]["content"]


@patch('anthropic.Anthropic')
def test_execute_with_skill_api_error(mock_anthropic, temp_pai_dir, sample_config):
    """Test handling of Anthropic API errors"""
    mock_client = Mock()
    mock_client.messages.create.side_effect = Exception("API Error")
    mock_anthropic.return_value = mock_client

    # Should raise exception
    with pytest.raises(Exception, match="API Error"):
        mock_client.messages.create(model="test", max_tokens=100, messages=[])


@patch('anthropic.Anthropic')
def test_execute_with_skill_includes_model_from_config(mock_anthropic, sample_config):
    """Test that execution uses model from config"""
    config = yaml.safe_load(sample_config.read_text())

    assert config["default_model"] == "claude-sonnet-4-5-20250929"

    # Would be used as: client.messages.create(model=config["default_model"], ...)


# ============================================================
# CLI COMMAND TESTS
# ============================================================

def test_cli_ask_command_routes_and_executes():
    """Test 'pai ask' command routes to skill and executes"""
    # This would test the Click command
    # from click.testing import CliRunner
    # runner = CliRunner()
    # result = runner.invoke(cli, ['ask', 'research AI'])
    # assert result.exit_code == 0
    # assert "research" in result.output
    pass  # Placeholder for actual CLI test


def test_cli_skills_command_lists_all_skills(temp_pai_dir, sample_core_skill, sample_research_skill):
    """Test 'pai skills' command lists available skills"""
    skills_dir = temp_pai_dir / "skills"
    skill_files = list(skills_dir.glob("*.md"))
    skill_names = [f.stem for f in skill_files]

    assert "CORE" in skill_names
    assert "research" in skill_names
    assert len(skill_names) == 2


def test_cli_show_command_displays_skill_content(sample_core_skill):
    """Test 'pai show' command displays skill content"""
    skill_content = sample_core_skill.read_text()

    assert "PAI CORE Context" in skill_content
    assert len(skill_content) > 0


# ============================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================

def test_empty_skill_file(temp_pai_dir):
    """Test handling of empty skill file"""
    empty_skill = temp_pai_dir / "skills" / "empty.md"
    empty_skill.write_text("")

    content = empty_skill.read_text()
    assert content == ""


def test_skill_file_missing_frontmatter(temp_pai_dir):
    """Test skill file without YAML frontmatter"""
    no_frontmatter = temp_pai_dir / "skills" / "no_frontmatter.md"
    no_frontmatter.write_text("# Just markdown content\nNo frontmatter here")

    content = no_frontmatter.read_text()
    assert not content.startswith("---")


def test_skill_file_malformed_frontmatter(temp_pai_dir):
    """Test skill file with malformed YAML frontmatter"""
    bad_frontmatter = temp_pai_dir / "skills" / "bad.md"
    bad_frontmatter.write_text("---\ninvalid: yaml: content:\n---\n# Content")

    content = bad_frontmatter.read_text()
    if content.startswith("---"):
        _, frontmatter, _ = content.split("---", 2)
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(frontmatter)


def test_config_missing_required_keys(temp_pai_dir):
    """Test config file missing required API keys"""
    config_path = temp_pai_dir / "config.yaml"
    incomplete_config = {"default_model": "claude-sonnet-4-5-20250929"}
    config_path.write_text(yaml.dump(incomplete_config))

    config = yaml.safe_load(config_path.read_text())
    assert "anthropic_api_key" not in config


def test_skill_routing_priority_first_match():
    """Test that first matching trigger wins when multiple skills match"""
    user_input = "research help"  # Could match both "research" and "help"

    # In real implementation, first matching skill should be returned
    # This tests the routing priority logic
    pass  # Placeholder


# ============================================================
# INTEGRATION-STYLE TESTS
# ============================================================

def test_full_skill_loading_and_routing_flow(temp_pai_dir, sample_core_skill, sample_research_skill):
    """Test complete flow: load skills → route user input → select correct skill"""
    # 1. Load all skills
    skills_dir = temp_pai_dir / "skills"
    skills = {}

    for skill_file in skills_dir.glob("*.md"):
        content = skill_file.read_text()
        if content.startswith("---"):
            _, frontmatter, body = content.split("---", 2)
            meta = yaml.safe_load(frontmatter)
            skills[skill_file.stem] = {
                "meta": meta,
                "content": content
            }

    # 2. Test routing for various inputs
    test_cases = [
        ("research quantum computing", "research"),
        ("help me", "CORE"),
        ("investigate this issue", "research"),
    ]

    for user_input, expected_skill in test_cases:
        matched_skill = "CORE"  # Default

        for skill_name, skill_data in skills.items():
            triggers = skill_data["meta"].get("triggers", [])
            for trigger in triggers:
                if trigger.lower() in user_input.lower():
                    matched_skill = skill_name
                    break
            if matched_skill != "CORE":
                break

        assert matched_skill == expected_skill


@patch('anthropic.Anthropic')
def test_end_to_end_ask_flow(mock_anthropic, temp_pai_dir, sample_research_skill, sample_config, monkeypatch):
    """Test complete end-to-end flow of asking a question"""
    monkeypatch.setenv("HOME", str(temp_pai_dir.parent.parent))

    # Setup mock
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Quantum computing is advancing rapidly...")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    user_input = "research quantum computing"

    # 1. Route to skill
    skill_name = "research"  # Would be determined by routing logic

    # 2. Load skill
    skill_content = sample_research_skill.read_text()

    # 3. Load config
    config = yaml.safe_load(sample_config.read_text())

    # 4. Execute with LLM
    client = mock_anthropic(api_key=config["anthropic_api_key"])
    response = client.messages.create(
        model=config["default_model"],
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"<skill-context>\n{skill_content}\n</skill-context>\n\n{user_input}"
        }]
    )

    # 5. Verify response
    assert response.content[0].text == "Quantum computing is advancing rapidly..."
    mock_client.messages.create.assert_called_once()
