---
name: sglang-log-analyze
description: |
  Analyze SGLang/LLM API request logs to extract system prompts and calculate token overhead. Use this skill when the user wants to:
  - Parse log files from LLM APIs (sglang, vLLM, OpenAI-compatible)
  - Find and analyze system prompt requests
  - Calculate token/character distribution of prompt components
  - Understand system prompt structure (tools, skills, instructions)
  - Generate analysis reports for prompt engineering optimization
  
  Trigger phrases: "analyze this log", "parse log file", "system prompt analysis", "token overhead", "prompt structure", "日志分析", "系统提示词开销"
---

# SGLang Log Analyzer

Analyzes LLM API request logs to extract system prompts and calculate token overhead distribution.

## Input

- **Log file path**: Path to a JSONL log file containing API requests
- **Request RID** (optional): Specific request ID to analyze; if not provided, analyzes the first `agent_request` type

## Output

- Analysis report in Markdown format with:
  - Request overview (type, tokens, latency)
  - System prompt structure breakdown
  - Token/character distribution by component
  - Tools JSONSchema details (for agent requests)

## Core Method: Finding System Prompt Requests

### Step 1: Locate API Request Events

Look for these event types in the log:
- `request.received` - Internal format with `text` field
- `request.received.openai` - OpenAI format with `messages` array

```python
# Pattern matching approach
for line in log_file:
    data = json.loads(line)
    event = data.get('event', '')
    obj = data.get('obj', {})
    
    if event in ('request.received', 'request.received.openai'):
        # Found a request
        pass
```

### Step 2: Identify Request Type

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

### Step 3: Parse System Prompt Structure

The `text` field follows a structured XML-like format:

```
<env>...</env>
<system>...</system>
<available_skills>...</available_skills>
<tools>...</tools>
<USER>...</USER>
<available_tools>...</available_tools>
```

**Extraction Pattern:**

```python
import re

def extract_components(text: str) -> dict:
    patterns = {
        'env': r'<env>(.*?)</env>',
        'system': r'<system>(.*?)</system>',
        'skills': r'<available_skills>(.*?)</available_skills>',
        'tools': r'<tools>(.*?)</tools>',
        'user': r'<USER>(.*?)</USER>',
    }
    
    components = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            components[name] = match.group(1)
    
    return components
```

### Step 4: Calculate Distribution

Calculate character count and estimated token ratio for each component:

```python
def calculate_distribution(components: dict, total_chars: int) -> list:
    distribution = []
    
    for name, content in components.items():
        chars = len(content)
        tokens_est = chars / 4.24  # English text ratio
        ratio = (chars / total_chars * 100) if total_chars > 0 else 0
        
        distribution.append({
            'component': name,
            'chars': chars,
            'tokens_est': int(tokens_est),
            'ratio': round(ratio, 1)
        })
    
    return sorted(distribution, key=lambda x: x['chars'], reverse=True)
```

## Tools Analysis (for agent_request type)

For agent requests, additionally analyze the Tools JSONSchema definitions:

### Extracting Individual Tool Definitions

```python
import json

def parse_tools_json(tools_text: str) -> list:
    """
    Parse tools from XML format.
    Input: '<toolcall>{"name": "...", "parameters": {...}}</toolcall>'
    """
    tools = []
    
    # Pattern to match JSON tool definitions within toolcall tags
    pattern = r'<toolcall>\s*(\{.*?\})\s*</toolcall>'
    matches = re.finditer(pattern, tools_text, re.DOTALL)
    
    for match in matches:
        try:
            tool_def = json.loads(match.group(1))
            tools.append(tool_def)
        except json.JSONDecodeError:
            continue
    
    return tools
```

### Tool Statistics

For each tool, calculate:
- Total characters
- Description length
- Number of parameters

```python
def analyze_tool(tool: dict) -> dict:
    name = tool.get('name', 'unknown')
    desc = tool.get('description', '')
    params = tool.get('parameters', {})
    param_count = len(params.get('properties', {}))
    
    return {
        'name': name,
        'total_chars': len(json.dumps(tool)),
        'desc_chars': len(desc),
        'param_count': param_count
    }
```

## Report Template

Generate a Markdown report with this structure:

```markdown
# {Service} Log Analysis Report

## 1. Request Overview

| Field | Value |
|-------|-------|
| RID | {rid} |
| Type | {request_type} |
| Prompt Tokens | {prompt_tokens} |
| Completion Tokens | {completion_tokens} |
| Time | {timestamp} |

## 2. System Prompt Structure

| Component | Characters | Est. Tokens | Ratio |
|-----------|------------|-------------|-------|
| {component} | {chars} | {tokens} | {ratio}% |

## 3. Detailed Analysis

### Tools Analysis (if agent_request)
- Total tools: {count}
- Total tools characters: {chars}

### Top 5 Tools by Size

| Tool | Total Chars | Description Chars | Params |
|------|-------------|-------------------|--------|
| {name} | {chars} | {desc_chars} | {count} |

## 4. Key Findings

1. {finding 1}
2. {finding 2}
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
