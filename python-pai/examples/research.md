---
name: research
triggers:
  - "research"
  - "investigate"
  - "find information"
  - "analyze trends"
  - "study"
  - "explore topic"
---

# Research Skill

## Purpose
Multi-source comprehensive research using web search and analysis.

## When to Activate
Use when user needs:
- Information gathering
- Trend analysis
- Comprehensive research
- Fact verification
- Topic exploration

## Workflow

### 1. Understand Request
Extract from user input:
- **Topic/question**: What are we researching?
- **Depth required**: Quick overview vs. comprehensive analysis?
- **Time constraints**: Urgent vs. thorough?
- **Format needed**: Summary, detailed report, bullet points?

### 2. Research Strategy
Choose approach based on request:

**Quick Research (5-10 min)**
- Single source or quick web search
- Surface-level findings
- Key facts only

**Medium Research (15-30 min)**
- Multiple sources (3-5)
- Cross-reference information
- Basic analysis

**Comprehensive Research (30+ min)**
- Extensive sources (10+)
- Deep analysis
- Multiple perspectives
- Detailed citations

### 3. Execute Research
For comprehensive research:
```bash
# Option 1: Use Claude's WebSearch
# Claude has built-in web search capabilities

# Option 2: Parallel agents (future)
# Launch multiple research agents in parallel
# pai delegate researcher --task "research {topic}"
```

### 4. Synthesize Findings
Combine results:
- Remove duplicates
- Identify patterns
- Note contradictions
- Cite sources
- Provide confidence levels

### 5. Structure Output
Format as:

```markdown
# Research: {Topic}

## Summary
[2-3 sentence overview]

## Key Findings
1. Finding 1 [Source]
2. Finding 2 [Source]
3. Finding 3 [Source]

## Detailed Analysis
[In-depth discussion of findings]

## Contradictions / Uncertainties
[Note any conflicting information]

## Recommendations
[Based on research, what should user do?]

## Sources
- [Source 1](URL)
- [Source 2](URL)
```

### 6. Capture to History
Save research to history:
```bash
pai-history research "{topic}" -c "$(cat research-findings.md)"
```

## Example Queries

**User:** "Research AI agent frameworks"
- Route to research skill
- Identify: comprehensive research needed
- Search for: frameworks, libraries, papers
- Analyze: features, tradeoffs, popularity
- Synthesize: comparison table + recommendations
- Capture to history/research/

**User:** "Quick overview of quantum computing"
- Route to research skill
- Identify: quick research needed
- Find: 2-3 authoritative sources
- Extract: key concepts, current state
- Format: bullet points
- Return summary

## Best Practices

1. **Always cite sources**: Every claim needs attribution
2. **Cross-reference**: Verify with multiple sources
3. **Note confidence**: High/Medium/Low for each finding
4. **Flag biases**: Identify potential source biases
5. **Timestamp**: Note when research was conducted
6. **Capture**: Always save to history for future reference

## Advanced Techniques

### Parallel Research (Future)
```python
import asyncio

async def parallel_research(topic):
    tasks = [
        research_web(topic),
        research_papers(topic),
        research_github(topic)
    ]
    results = await asyncio.gather(*tasks)
    return synthesize(results)
```

### Citation Tracking
- Keep source URLs
- Note publication dates
- Track author credentials
- Record access date

### Confidence Scoring
- High (90%+): Multiple authoritative sources agree
- Medium (60-90%): Some sources, or single authoritative
- Low (<60%): Single source, outdated, or contradictory

## Related Skills

- **CORE**: General questions and guidance
- **analysis**: Deep analysis of research findings (future)
- **writing**: Turn research into blog posts/articles (future)

## Tools Integration

- **WebSearch**: Claude's built-in web search
- **WebFetch**: Fetch specific URLs
- **pai-history**: Save research findings
- **pai-voice**: Announce completion

## Completion Format

When research is complete, use:

```markdown
🎯 COMPLETED: Research on {topic} finished with {N} sources
```

This triggers voice feedback if configured.
