---
name: sglang-log-analyze
description: |
  Analyze SGLang/LLM API request logs to extract system prompts and calculate token overhead. Use this skill when the user wants to:
  - Parse log files from LLM APIs (sglang, vLLM, OpenAI-compatible)
  - Segment user questions from logs (time-gap based)
  - Find and analyze system prompt requests
  - Calculate token/character distribution of prompt components
  - Understand system prompt structure (tools, skills, instructions)
  - Generate analysis reports for prompt engineering optimization
  
  Trigger phrases: "analyze this log", "parse log file", "segment questions", "user questions", "system prompt analysis", "token overhead", "prompt structure", "日志分析", "系统提示词开销", "用户问题分割"
---

# SGLang Log Analyzer

Analyzes LLM API request logs to extract system prompts and calculate token overhead distribution.

## Input

- **Log file path**: Path to a JSONL log file containing API requests
- **Request RID** (optional): Specific request ID to analyze; if not provided, analyzes the first `agent_request` type

## Output

- Analysis report in Markdown format with:
  - **User questions segmentation** (by time gap)
  - **System prompt deep analysis** (combined):
    - Request type identification
    - Structure parsing (sections, components)
    - Token/character distribution
    - Tools analysis (count, size, categories)
    - Skills analysis (metadata, list)

## Step 1: Segment User Questions (Always Do First)

**Important**: Before analyzing system prompts, segment the log into user questions using time-gap detection.

### Method: Time-Gap Based Segmentation

When two consecutive `request.received.openai` events have a time gap > 60 seconds, they represent different user questions.

```python
from pathlib import Path
from datetime import datetime
import json

def segment_user_questions(log_path: str, time_gap_threshold: float = 60.0) -> list:
    """
    Segment log into user questions based on time gap.
    
    Args:
        log_path: Path to JSONL log file
        time_gap_threshold: Seconds between requests to consider new question (default: 60s)
    
    Returns:
        List of question groups, each containing multiple API call events
    """
    lines = Path(log_path).read_text(encoding='utf-8').splitlines()
    
    # Parse all events
    events = []
    for line in lines:
        try:
            events.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            continue
    
    # Group events by session (each request.received.openai starts a new session)
    sessions = []
    current_session = []
    
    for e in events:
        if e.get('event') == 'request.received.openai':
            if current_session:
                sessions.append(current_session)
            current_session = [e]
        elif e.get('event') == 'request.finished':
            current_session.append(e)
    
    if current_session:
        sessions.append(current_session)
    
    # Extract user messages from agent_request sessions
    user_questions = []
    for session in sessions:
        req_openai = session[0]
        messages = req_openai.get('obj', {}).get('messages', [])
        
        for msg in messages:
            if msg.get('role') == 'system':
                content = msg.get('content', '')
                # Only process agent requests (exclude title_generator)
                if 'opencode' in content.lower() and 'title generator' not in content.lower():
                    # Find last user message
                    for m in reversed(messages):
                        if m.get('role') == 'user':
                            user_questions.append({
                                'timestamp': req_openai.get('timestamp', ''),
                                'session': session,
                                'user_message': m.get('content', '')
                            })
                            break
                break
    
    # Group by time gap
    question_groups = []
    current_group = []
    prev_ts = None
    
    for q in user_questions:
        ts = datetime.fromisoformat(q['timestamp'][:19])
        if prev_ts:
            diff = (ts - prev_ts).total_seconds()
            if diff > time_gap_threshold:
                if current_group:
                    question_groups.append(current_group)
                current_group = [q]
            else:
                current_group.append(q)
        else:
            current_group = [q]
        prev_ts = ts
    
    if current_group:
        question_groups.append(current_group)
    
    return question_groups
```

### Output Format

```markdown
# User Questions Segmentation Report

## Summary
- Total sessions: {count}
- Total user questions: {count}
- Question groups (time gap > {threshold}s): {count}

## Question 1
- Timestamp: {timestamp}
- API calls: {count}

### User Question:
{user_message_text}

---
```

## Step 1.2: Generate Detailed Statistics Report

Generate detailed per-question statistics including tokens and tool calls.

### Method

```python
from pathlib import Path
from datetime import datetime
import json

def generate_detailed_stats(log_path: str, time_gap_threshold: float = 60.0) -> str:
    """
    Generate detailed statistics report for user questions.
    
    Returns Markdown report with:
    - Per-question LLM call count
    - Per-question Tool call count
    - Per-call prompt/completion tokens
    - Token consumption ranking
    """
    lines = Path(log_path).read_text(encoding='utf-8').splitlines()
    
    events = []
    for line in lines:
        try:
            events.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            continue
    
    # Pair request.received.openai with request.finished
    sessions = []
    pending_openai = None
    
    for e in events:
        if e.get('event') == 'request.received.openai':
            pending_openai = e
        elif e.get('event') == 'request.finished' and pending_openai:
            meta_info = e.get('out', {}).get('meta_info', {})
            sessions.append({
                'timestamp': pending_openai.get('timestamp', ''),
                'messages': pending_openai.get('obj', {}).get('messages', []),
                'prompt_tokens': meta_info.get('prompt_tokens', 0),
                'completion_tokens': meta_info.get('completion_tokens', 0)
            })
            pending_openai = None
    
    # Filter agent_request sessions
    agent_sessions = []
    for sess in sessions:
        messages = sess.get('messages', [])
        user_msg = ''
        tool_count = 0
        
        for msg in messages:
            role = msg.get('role', '')
            if role == 'system':
                content = msg.get('content', '')
                if 'opencode' in content.lower() and 'title generator' not in content.lower():
                    sess['is_agent'] = True
            elif role == 'user':
                user_msg = msg.get('content', '')
            elif role == 'tool':
                tool_count += 1
        
        if sess.get('is_agent', False):
            sess['user_message'] = user_msg
            sess['tool_count'] = tool_count
            agent_sessions.append(sess)
    
    # Group by time gap
    prev_ts = None
    question_groups = []
    current_group = []
    
    for sess in agent_sessions:
        ts = datetime.fromisoformat(sess['timestamp'][:19])
        if prev_ts:
            diff = (ts - prev_ts).total_seconds()
            if diff > time_gap_threshold:
                if current_group:
                    question_groups.append(current_group)
                current_group = [sess]
            else:
                current_group.append(sess)
        else:
            current_group = [sess]
        prev_ts = ts
    
    if current_group:
        question_groups.append(current_group)
    
    # Generate report...
    return report
```

### Report Template

```markdown
# SGLang Log 用户问题详细统计分析

## 统计摘要
| 指标 | 值 |
|------|-----|
| 总 API 会话数 | {total_sessions} |
| Agent 请求数 | {agent_count} |
| 用户问题数 | {question_count} |
| 总 LLM 调用次数 | {llm_count} |
| 总 Tool 调用次数 | {tool_count} |
| 总输入 Tokens | {total_prompt} |
| 总输出 Tokens | {total_completion} |

## 问题 1
**时间**: {timestamp}
**用户问题**: {preview}

### 统计信息
| 指标 | 值 |
|------|-----|
| LLM 调用次数 | {llm_count} |
| Tool 调用次数 | {tool_count} |
| 输入 Tokens 总计 | {prompt} |
| 输出 Tokens 总计 | {completion} |

### 每次 LLM 调用详情
| # | 时间戳 | Prompt Tokens | Completion Tokens | Tool Calls |
|---|--------|---------------|-------------------|------------|
| 1 | ... | ... | ... | ... |

## Token 消耗排名
| 排名 | 问题 | 输入 Tokens | 输出 Tokens | 总 Tokens |
|------|------|-------------|-------------|-----------|
```

## Step 2: System Prompt Deep Analysis

A combined analysis that covers request type identification, structure parsing, token distribution, and tools analysis.

### 2.1 Identify Request Type

Determine the request type by examining system prompt content:

| System Prompt Keywords | Request Type | Description |
|------------------------|--------------|-------------|
| `opencode` + `interactive cli` | `agent_request` | Agent main request with full tools |
| `skill` + `load/trigger` | `skill_load` | SKILL selection/loading |
| `title generator` | `title_generation` | Conversation title generation |
| `summariz` / `translation` | `task_request` | Sub-task requests |

```python
def identify_request_type(system_prompt: str) -> str:
    prompt_lower = system_prompt.lower()
    
    if 'opencode' in prompt_lower and 'interactive cli' in prompt_lower:
        return 'agent_request'
    elif 'skill' in prompt_lower and ('load' in prompt_lower or 'trigger' in prompt_lower):
        return 'skill_load'
    elif 'title generator' in prompt_lower:
        return 'title_generation'
    else:
        return 'general'
```

### 2.2 Parse System Prompt Structure

The system prompt can be divided into sections by the `Instructions from:` marker:

```
┌─────────────────────────────────────────────────────────────────────┐
│ SECTION 1: Base Instructions                                        │
│ "You are opencode, an interactive CLI tool..."                      │
│ - Role definition, core behavior rules, tone guidelines             │
├─────────────────────────────────────────────────────────────────────┤
│ SECTION 2: Global Rules (after "Instructions from:" marker)         │
│ Path + brief rules in Chinese                                       │
├─────────────────────────────────────────────────────────────────────┤
│ SECTION 3: Project Context                                          │
│ - AGENTS.md content (project-specific instructions)                 │
│ - Build/Lint/Test Commands                                          │
│ - Code Style Guidelines                                             │
│ - Dependencies                                                      │
│ - <available_skills>...</available_skills>                          │
│ - <available_tools>...</available_tools>                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Extraction Method:**

```python
def analyze_system_prompt(content: str) -> dict:
    """
    Deep analysis of system prompt structure.
    
    Returns:
        dict with sections, components, tools, skills analysis
    """
    result = {
        'total_chars': len(content),
        'sections': {},
        'tools': [],
        'skills': [],
        'distribution': []
    }
    
    # Split by "Instructions from:" marker
    marker = 'Instructions from:'
    parts = content.split(marker)
    
    result['sections']['base_instructions'] = parts[0]  # ~8-9K chars
    result['sections']['global_rules'] = parts[1] if len(parts) > 1 else ''
    result['sections']['project_context'] = parts[2] if len(parts) > 2 else ''
    
    # Extract available_skills
    skills_start = content.find('<available_skills>')
    skills_end = content.find('</available_skills>')
    if skills_start > 0 and skills_end > 0:
        skills_xml = content[skills_start:skills_end + len('</available_skills>')]
        result['sections']['available_skills'] = skills_xml
        
        # Parse skill names
        import re
        skill_names = re.findall(r'<name>([^<]+)</name>', skills_xml)
        result['skills'] = skill_names
    
    return result
```

### 2.3 Calculate Component Distribution

Calculate character count and ratio for each component:

```python
def calculate_distribution(sections: dict, total_chars: int) -> list:
    """
    Calculate character distribution across sections.
    
    Args:
        sections: Dict of section_name -> section_content
        total_chars: Total system prompt length
    
    Returns:
        Sorted list of (section_name, chars, ratio)
    """
    distribution = []
    
    for name, content in sections.items():
        chars = len(content)
        ratio = (chars / total_chars * 100) if total_chars > 0 else 0
        
        distribution.append({
            'section': name,
            'chars': chars,
            'ratio': round(ratio, 1)
        })
    
    return sorted(distribution, key=lambda x: x['chars'], reverse=True)
```

### 2.4 Tools Analysis (for agent_request type)

For agent requests, analyze the Tools JSONSchema definitions from `messages[0].tools`:

```python
import json

def analyze_tools(tools: list) -> dict:
    """
    Analyze tool definitions from request.
    
    Args:
        tools: List of tool definitions from API request
    
    Returns:
        dict with tool statistics, sizes, categories
    """
    result = {
        'total_count': len(tools),
        'total_chars': 0,
        'tools': [],
        'categories': {}
    }
    
    for tool in tools:
        # Handle both OpenAI and custom formats
        func = tool.get('function', tool)
        name = func.get('name', 'unknown')
        tool_json = json.dumps(tool, ensure_ascii=False)
        size = len(tool_json)
        
        result['total_chars'] += size
        result['tools'].append({
            'name': name,
            'size': size,
            'desc_len': len(func.get('description', '')),
            'param_count': len(func.get('parameters', {}).get('properties', {}))
        })
        
        # Categorize by name pattern
        if 'Read' in name:
            cat = 'Read'
        elif 'Edit' in name or 'Write' in name:
            cat = 'Edit/Write'
        elif 'Bash' in name or 'bash' in name:
            cat = 'Execution'
        elif 'Grep' in name or 'Glob' in name:
            cat = 'Search'
        elif 'team' in name:
            cat = 'Team'
        elif 'skill' in name:
            cat = 'Skill'
        else:
            cat = 'Other'
        
        result['categories'][cat] = result['categories'].get(cat, 0) + 1
    
    # Sort tools by size
    result['tools'].sort(key=lambda x: x['size'], reverse=True)
    
    return result
```

### 2.5 Skills Analysis

Analyze skill metadata from `<available_skills>`:

```python
import re

def analyze_skills(content: str) -> dict:
    """
    Analyze skills from available_skills section.
    
    Returns:
        dict with skill list, metadata sizes, total chars
    """
    skills_start = content.find('<available_skills>')
    skills_end = content.find('</available_skills>')
    
    if skills_start < 0:
        return {'skills': [], 'total_chars': 0}
    
    skills_xml = content[skills_start:skills_end + len('</available_skills>')]
    
    # Extract skill info
    skill_names = re.findall(r'<name>([^<]+)</name>', skills_xml)
    skill_descriptions = re.findall(r'<description>([^<]+)</description>', skills_xml)
    skill_locations = re.findall(r'<location>([^<]+)</location>', skills_xml)
    
    # Calculate per-skill metadata sizes
    skill_sizes = []
    for name in skill_names:
        name_pattern = '<name>%s</name>' % name
        start = skills_xml.find(name_pattern)
        end = skills_xml.find('</skill>', start)
        if start >= 0 and end > start:
            size = end - start + len('</skill>')
            skill_sizes.append({'name': name, 'metadata_size': size})
    
    return {
        'skills': skill_names,
        'skill_count': len(skill_names),
        'total_chars': len(skills_xml),
        'skill_sizes': skill_sizes
    }
```

## Step 2.6: Complete Deep Analysis Report Template

Generate a comprehensive Markdown report combining all analyses:

```markdown
# System Prompt Deep Analysis Report

## Summary

| Metric | Value |
|--------|-------|
| Total System Prompt Length | {total_chars} chars |
| Request Type | {request_type} |
| Base Instructions | {base_chars} chars ({base_ratio}%) |
| Global Rules | {rules_chars} chars ({rules_ratio}%) |
| Project Context | {context_chars} chars ({context_ratio}%) |
| Available Skills | {skill_count} skills |
| Available Tools | {tool_count} tools |

## 1. System Prompt Structure Overview

### 1.1 Section Breakdown

| Section | Characters | Ratio |
|---------|------------|-------|
| Base Instructions | {base_chars} | {base_ratio}% |
| Global Rules | {rules_chars} | {rules_ratio}% |
| Project Context | {context_chars} | {context_ratio}% |

### 1.2 Project Context Breakdown

| Subsection | Characters | Notes |
|------------|------------|-------|
| AGENTS.md Header | {header_chars} | Title + description |
| Build/Lint/Test Commands | ~{build_chars} | Instructions for running code |
| Code Style Guidelines | ~{style_chars} | Python style conventions |
| Dependencies | ~{deps_chars} | Package list |
| Available Skills | {skills_chars} | {skill_count} skills metadata |

## 2. Available Skills Analysis

### 2.1 Skill List ({skill_count} total)

| # | Skill Name | Metadata Size | Description |
|---|------------|---------------|-------------|
| 1 | {skill_name} | {size} chars | {desc_preview} |
| ... | ... | ... | ... |

### 2.2 Skills Metadata Structure

```xml
<available_skills>
  <skill>
    <name>skill-name</name>
    <description>Skill description...</description>
    <location>file:///path/to/SKILL.md</location>
  </skill>
</available_skills>
```

## 3. Available Tools Analysis

### 3.1 Tool Overview

| Metric | Value |
|--------|-------|
| Total Tools | {tool_count} |
| Total Tools JSON Size | {tool_total_chars} chars |
| Average per Tool | {avg_tool_size} chars |
| Largest Tool | {largest_tool} ({largest_size} chars) |
| Smallest Tool | {smallest_tool} ({smallest_size} chars) |

### 3.2 Top 10 Tools by Size

| Rank | Tool Name | Size (chars) |
|------|-----------|--------------|
| 1 | {name} | {size} |
| ... | ... | ... |

### 3.3 Tool Categories

| Category | Count | Tools |
|----------|-------|-------|
| Read | {read_count} | read |
| Edit/Write | {edit_count} | edit, write |
| Execution | {exec_count} | bash, task |
| Search | {search_count} | grep, glob |
| Team | {team_count} | team_* functions |
| Skill | {skill_func_count} | skill_* functions |
| Other | {other_count} | Various utilities |

### 3.4 Tool JSON Structure

```json
{
  "description": "Tool description with usage notes...",
  "name": "tool_name",
  "parameters": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
      "param1": { "type": "string", "description": "..." }
    },
    "required": ["param1"]
  }
}
```

## 4. Token Cost Analysis

| Metric | Value |
|--------|-------|
| Actual prompt_tokens | {prompt_tokens} |
| Est. chars per token (EN) | ~4.0 |
| System Prompt chars | {total_chars} |
| Est. System Prompt Tokens | ~{est_tokens} |

## 5. Key Findings & Optimization Opportunities

### 5.1 Potential Reductions

| Component | Current | Potential | Savings |
|-----------|---------|-----------|---------|
| Base Instructions | {base_chars} | ~{target_base} | ~{savings_base} |
| Repeated Examples | ~{examples_chars} | ~500 | ~{savings_examples} |
| Tool descriptions | {tool_total_chars} | ~{target_tools} | ~{savings_tools} |

### 5.2 Recommendations

1. **{recommendation_1}**
2. **{recommendation_2}**
3. **{recommendation_3}**
```

## Usage Example

```bash
# Run the analysis script
python scripts/analyze_log.py /path/to/logfile.log --rid <optional-rid>

# Or analyze inline using Bash tool
python -c "
import json
import re

with open('logfile.log', 'r') as f:
    for line in f:
        data = json.loads(line)
        if data.get('event') == 'request.received':
            text = data.get('obj', {}).get('text', '')
            # Extract and analyze components...
"
```

## Output Location

Save reports to:
- `agent_analysis/output/log_analysis_{timestamp}.md`
- Console output for quick inspection

## Dependencies

- Python 3.8+
- Standard library: `json`, `re`, `pathlib`, `datetime`
- No external dependencies required
