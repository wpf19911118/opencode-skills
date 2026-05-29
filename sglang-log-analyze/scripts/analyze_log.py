#!/usr/bin/env python3
"""
SGLang Log Analyzer

Analyzes LLM API request logs to extract system prompts and calculate token overhead.

Usage:
    python analyze_log.py <log_file> [--rid <request_id>] [--output <output_dir>]
    python analyze_log.py <log_file> --segment                    # Segment user questions
    python analyze_log.py <log_file> --segment --output <dir>     # Save segmentation report
"""

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, NamedTuple


@dataclass
class QuestionGroup:
    """A group of API calls representing one user question"""
    timestamp: str
    api_calls: int
    user_message: str
    session_index: int


class Session(NamedTuple):
    """A single API session (request.received.openai + request.finished)"""
    rid: str
    timestamp: str
    request_type: str
    user_message: str


def segment_user_questions(log_path: str, time_gap_threshold: float = 60.0) -> tuple[list[Session], list[QuestionGroup]]:
    """
    Segment log into user questions based on time gap.
    
    Args:
        log_path: Path to JSONL log file
        time_gap_threshold: Seconds between requests to consider new question (default: 60s)
    
    Returns:
        Tuple of (sessions, question_groups)
    """
    lines = Path(log_path).read_text(encoding="utf-8").splitlines()
    
    events = []
    for line in lines:
        try:
            events.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            continue
    
    # Group events by session
    sessions = []
    current_session = []
    
    for e in events:
        if e.get("event") == "request.received.openai":
            if current_session:
                sessions.append(current_session)
            current_session = [e]
        elif e.get("event") == "request.finished":
            current_session.append(e)
    
    if current_session:
        sessions.append(current_session)
    
    # Extract sessions with user messages
    extracted_sessions = []
    for session in sessions:
        req_openai = session[0]
        messages = req_openai.get("obj", {}).get("messages", [])
        
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                # Only process agent requests (exclude title_generator)
                if "opencode" in content.lower() and "title generator" not in content.lower():
                    # Find last user message
                    for m in reversed(messages):
                        if m.get("role") == "user":
                            extracted_sessions.append(Session(
                                rid=req_openai.get("obj", {}).get("rid", ""),
                                timestamp=req_openai.get("timestamp", ""),
                                request_type="agent_request",
                                user_message=m.get("content", "")
                            ))
                            break
                    break
    
    # Group by time gap
    question_groups = []
    current_group = []
    prev_ts = None
    
    for sess in extracted_sessions:
        ts = datetime.fromisoformat(sess.timestamp[:19])
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
    
    return extracted_sessions, question_groups


def generate_segmentation_report(log_path: str, time_gap: float = 60.0) -> str:
    """Generate user questions segmentation report"""
    sessions, question_groups = segment_user_questions(log_path, time_gap)
    
    report = []
    report.append("# User Questions Segmentation Report\n")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    report.append("## Summary\n\n")
    report.append(f"- **Total sessions**: {len(sessions)}\n")
    report.append(f"- **Question groups** (time gap > {time_gap}s): {len(question_groups)}\n")
    report.append(f"- **Time gap threshold**: {time_gap}s\n\n")
    
    for gi, group in enumerate(question_groups, 1):
        first_sess = group[0]
        report.append("---\n\n")
        report.append(f"## Question {gi}\n\n")
        report.append(f"- **Timestamp**: {first_sess.timestamp[:19]}\n")
        report.append(f"- **API calls**: {len(group)}\n")
        report.append("\n### User Question:\n\n")
        report.append(first_sess.user_message[:500])
        if len(first_sess.user_message) > 500:
            report.append("\n```\n[truncated...]\n```")
        report.append("\n")
    
    report.append("\n---\n")
    report.append("*Report generated by sglang-log-analyze skill*\n")
    
    return "".join(report)


def generate_detailed_stats_report(log_path: str, time_gap: float = 60.0) -> str:
    """Generate detailed statistics report with per-call token info"""
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
            if diff > time_gap:
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
    
    # Generate report
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_llm = len(agent_sessions)
    total_tools = sum(s['tool_count'] for s in agent_sessions)
    total_prompt = sum(s['prompt_tokens'] for s in agent_sessions)
    total_completion = sum(s['completion_tokens'] for s in agent_sessions)
    
    report = []
    report.append("# SGLang Log 用户问题详细统计分析\n")
    report.append("\n")
    report.append(f"**Generated**: {now_str}\n")
    report.append("\n---\n")
    report.append("\n## 统计摘要\n")
    report.append("\n")
    report.append("| 指标 | 值 |\n")
    report.append("|------|----|\n")
    report.append(f"| 总 API 会话数 | {len(sessions)} |\n")
    report.append(f"| Agent 请求数 | {total_llm} |\n")
    report.append(f"| 用户问题数 | {len(question_groups)} |\n")
    report.append(f"| 总 LLM 调用次数 | {total_llm} |\n")
    report.append(f"| 总 Tool 调用次数 | {total_tools} |\n")
    report.append(f"| 总输入 Tokens | {total_prompt:,} |\n")
    report.append(f"| 总输出 Tokens | {total_completion:,} |\n")
    report.append(f"| 总 Tokens 消耗 | {total_prompt + total_completion:,} |\n")
    report.append(f"| 平均输入/次 | {total_prompt // total_llm if total_llm > 0 else 0:,} |\n")
    report.append(f"| 平均输出/次 | {total_completion // total_llm if total_llm > 0 else 0:,} |\n")
    report.append("\n")
    
    for gi, group in enumerate(question_groups, 1):
        first = group[0]
        report.append("---\n")
        report.append("\n")
        report.append(f"## 问题 {gi}\n")
        report.append("\n")
        report.append(f"**时间**: {first['timestamp'][:19]}\n")
        report.append("\n")
        report.append("**用户问题** (前200字):\n")
        report.append("\n")
        preview = first['user_message'][:200]
        if len(first['user_message']) > 200:
            preview += '...'
        report.append("```\n")
        report.append(preview + "\n")
        report.append("```\n")
        report.append("\n")
        
        q_llm = len(group)
        q_tools = sum(s['tool_count'] for s in group)
        q_prompt = sum(s['prompt_tokens'] for s in group)
        q_completion = sum(s['completion_tokens'] for s in group)
        q_total = q_prompt + q_completion
        avg_prompt = q_prompt // q_llm if q_llm > 0 else 0
        avg_completion = q_completion // q_llm if q_llm > 0 else 0
        
        report.append("### 统计信息\n")
        report.append("\n")
        report.append("| 指标 | 值 |\n")
        report.append("|------|----|\n")
        report.append(f"| LLM 调用次数 | {q_llm} |\n")
        report.append(f"| Tool 调用次数 | {q_tools} |\n")
        report.append(f"| 输入 Tokens 总计 | {q_prompt:,} |\n")
        report.append(f"| 输出 Tokens 总计 | {q_completion:,} |\n")
        report.append(f"| Tokens 总消耗 | {q_total:,} |\n")
        report.append(f"| 平均每次输入 Tokens | {avg_prompt:,} |\n")
        report.append(f"| 平均每次输出 Tokens | {avg_completion:,} |\n")
        report.append("\n")
        
        report.append("### 每次 LLM 调用详情\n")
        report.append("\n")
        report.append("| # | 时间戳 | Prompt Tokens | Completion Tokens | 总 Tokens | Tool Calls |\n")
        report.append("|---|--------|---------------|-------------------|-----------|------------|\n")
        
        for ci, sess in enumerate(group, 1):
            ts = sess['timestamp'][11:19]
            call_total = sess['prompt_tokens'] + sess['completion_tokens']
            report.append(f"| {ci} | {ts} | {sess['prompt_tokens']:,} | {sess['completion_tokens']:,} | {call_total:,} | {sess['tool_count']} |\n")
        
        report.append("\n")
    
    # Token consumption ranking
    report.append("---\n")
    report.append("\n## Token 消耗排名 (按问题)\n")
    report.append("\n")
    report.append("| 排名 | 问题 | 输入 Tokens | 输出 Tokens | 总 Tokens |\n")
    report.append("|------|------|-------------|-------------|-----------|\n")
    
    ranked = []
    for gi, group in enumerate(question_groups, 1):
        total = sum(s['prompt_tokens'] + s['completion_tokens'] for s in group)
        prompt = sum(s['prompt_tokens'] for s in group)
        completion = sum(s['completion_tokens'] for s in group)
        ranked.append((gi, total, prompt, completion))
    
    ranked.sort(key=lambda x: x[1], reverse=True)
    for rank, (gi, total, prompt, completion) in enumerate(ranked, 1):
        report.append(f"| {rank} | 问题 {gi} | {prompt:,} | {completion:,} | {total:,} |\n")
    
    report.append("\n---\n")
    report.append("\n*报告由 sglang-log-analyze 技能生成*\n")
    
    return "".join(report)


@dataclass
class RequestRecord:
    """Request record from log file"""
    rid: str
    event: str
    timestamp: str
    request_type: str = "unknown"
    description: str = ""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    system_prompt: str = ""
    components: dict = field(default_factory=dict)
    tools: list = field(default_factory=list)


def identify_request_type(system_prompt: str) -> tuple[str, str]:
    """Identify request type from system prompt content"""
    prompt_lower = system_prompt.lower()
    
    if not system_prompt:
        return "unknown", "Empty prompt"
    
    if "opencode" in prompt_lower and "interactive cli" in prompt_lower:
        return "agent_request", "Agent main request with full tools"
    elif "skill" in prompt_lower and ("load" in prompt_lower or "trigger" in prompt_lower):
        return "skill_load", "SKILL selection/loading"
    elif "title generator" in prompt_lower:
        return "title_generation", "Conversation title generation"
    elif "summariz" in prompt_lower:
        return "summarization", "Summary generation"
    elif "translation" in prompt_lower or "translat" in prompt_lower:
        return "translation", "Translation task"
    else:
        return "general", "General request"


def extract_components(text: str) -> dict:
    """Extract structured components from text using regex patterns"""
    patterns = {
        "env": r"<env>(.*?)</env>",
        "system": r"<system>(.*?)</system>",
        "available_skills": r"<available_skills>(.*?)</available_skills>",
        "tools": r"<tools>(.*?)</tools>",
        "user": r"<USER>(.*?)</USER>",
    }
    
    components = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            components[name] = match.group(1)
    
    return components


def parse_tools_json(tools_text: str) -> list:
    """Parse tool definitions from tools section"""
    tools = []
    
    pattern = r'<toolcall>\s*(\{.*?\})\s*</toolcall>'
    matches = re.finditer(pattern, tools_text, re.DOTALL)
    
    for match in matches:
        try:
            tool_def = json.loads(match.group(1))
            tools.append(tool_def)
        except json.JSONDecodeError:
            continue
    
    return tools


def analyze_tool(tool: dict) -> dict:
    """Analyze individual tool definition"""
    name = tool.get("name", "unknown")
    desc = tool.get("description", "")
    params = tool.get("parameters", {})
    param_count = len(params.get("properties", {}))
    
    return {
        "name": name,
        "total_chars": len(json.dumps(tool)),
        "desc_chars": len(desc),
        "param_count": param_count,
        "tool_def": tool
    }


def calculate_distribution(components: dict, total_chars: int) -> list:
    """Calculate character distribution across components"""
    distribution = []
    
    for name, content in components.items():
        chars = len(content)
        tokens_est = int(chars / 4.24)
        ratio = round(chars / total_chars * 100, 1) if total_chars > 0 else 0
        
        distribution.append({
            "component": name,
            "chars": chars,
            "tokens_est": tokens_est,
            "ratio": ratio
        })
    
    return sorted(distribution, key=lambda x: x["chars"], reverse=True)


def parse_log_file(log_path: str, target_rid: Optional[str] = None) -> list[RequestRecord]:
    """Parse log file and extract request records
    
    Note: System prompt is stored in request.finished event's obj.text field (decoded),
    not in request.received event.
    """
    records = {}
    
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                event = data.get("event", "")
                obj = data.get("obj", {})
                
                rid = obj.get("rid", "N/A")
                
                if event == "request.received":
                    if target_rid and rid != target_rid:
                        continue
                    
                    input_ids = obj.get("input_ids")
                    records[rid] = RequestRecord(
                        rid=rid,
                        event=event,
                        timestamp=data.get("timestamp", ""),
                        request_type="pending",
                        description="Waiting for system prompt",
                    )
                    
                elif event == "request.finished":
                    finished_text = obj.get("text", "")
                    if target_rid and rid != target_rid:
                        continue
                    
                    if rid in records:
                        records[rid].event = event
                        records[rid].timestamp = data.get("timestamp", "")
                        records[rid].system_prompt = finished_text
                        
                        if finished_text:
                            request_type, description = identify_request_type(finished_text)
                            records[rid].request_type = request_type
                            records[rid].description = description
                            records[rid].components = extract_components(finished_text)
                            
                            if "tools" in records[rid].components:
                                records[rid].tools = parse_tools_json(records[rid].components["tools"])
                        
                        meta_info = data.get("out", {}).get("meta_info", {})
                        records[rid].prompt_tokens = meta_info.get("prompt_tokens")
                        records[rid].completion_tokens = meta_info.get("completion_tokens")
                    else:
                        if target_rid and rid != target_rid:
                            continue
                        
                        if finished_text:
                            request_type, description = identify_request_type(finished_text)
                            components = extract_components(finished_text)
                            tools = []
                            if "tools" in components:
                                tools = parse_tools_json(components["tools"])
                            
                            meta_info = data.get("out", {}).get("meta_info", {})
                            
                            records[rid] = RequestRecord(
                                rid=rid,
                                event=event,
                                timestamp=data.get("timestamp", ""),
                                request_type=request_type,
                                description=description,
                                system_prompt=finished_text,
                                components=components,
                                tools=tools,
                                prompt_tokens=meta_info.get("prompt_tokens"),
                                completion_tokens=meta_info.get("completion_tokens")
                            )
                            
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    
    return sorted(records.values(), key=lambda x: x.timestamp)


def generate_report(record: RequestRecord) -> str:
    """Generate Markdown analysis report"""
    total_chars = len(record.system_prompt)
    distribution = calculate_distribution(record.components, total_chars)
    
    report = []
    report.append("# System Prompt Analysis Report\n")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    report.append("## 1. Request Overview\n\n")
    report.append(f"| Field | Value |\n")
    report.append(f"|-------|-------|\n")
    report.append(f"| RID | `{record.rid}` |\n")
    report.append(f"| Type | `{record.request_type}` |\n")
    report.append(f"| Description | {record.description} |\n")
    report.append(f"| Timestamp | {record.timestamp} |\n")
    report.append(f"| Prompt Tokens | {record.prompt_tokens or 'N/A'} |\n")
    report.append(f"| Completion Tokens | {record.completion_tokens or 'N/A'} |\n")
    report.append(f"| Total Characters | {total_chars:,} |\n")
    report.append(f"| Est. Total Tokens | ~{int(total_chars / 4.24):,} |\n\n")
    
    report.append("## 2. Component Distribution\n\n")
    report.append(f"| Component | Characters | Est. Tokens | Ratio |\n")
    report.append(f"|-----------|------------|-------------|-------|\n")
    for item in distribution:
        report.append(f"| {item['component']} | {item['chars']:,} | ~{item['tokens_est']:,} | {item['ratio']}% |\n")
    report.append("\n")
    
    if record.tools:
        report.append("## 3. Tools Analysis\n\n")
        report.append(f"**Total Tools**: {len(record.tools)}\n\n")
        
        tool_stats = [analyze_tool(t) for t in record.tools]
        tool_stats.sort(key=lambda x: x["total_chars"], reverse=True)
        
        total_tool_chars = sum(t["total_chars"] for t in tool_stats)
        total_desc_chars = sum(t["desc_chars"] for t in tool_stats)
        
        report.append(f"| Metric | Value |\n")
        report.append(f"|--------|-------|\n")
        report.append(f"| Total tool definitions | {len(record.tools)} |\n")
        report.append(f"| Total characters | {total_tool_chars:,} |\n")
        report.append(f"| Description characters | {total_desc_chars:,} |\n\n")
        
        report.append("### Top 5 Tools by Size\n\n")
        report.append(f"| # | Tool | Total Chars | Desc Chars | Params |\n")
        report.append(f"|---|------|-------------|------------|--------|\n")
        for i, tool in enumerate(tool_stats[:5], 1):
            report.append(f"| {i} | `{tool['name']}` | {tool['total_chars']:,} | {tool['desc_chars']:,} | {tool['param_count']} |\n")
        report.append("\n")
        
        report.append("### All Tools\n\n")
        for i, tool in enumerate(tool_stats, 1):
            report.append(f"{i}. `{tool['name']}` - {tool['total_chars']:,} chars, {tool['param_count']} params\n")
        report.append("\n")
    
    report.append("## 4. Key Findings\n\n")
    
    if distribution:
        largest = distribution[0]
        report.append(f"1. **Largest component**: `{largest['component']}` at {largest['ratio']}% ({largest['chars']:,} chars)\n")
    
    if record.tools:
        report.append(f"2. **Tools overhead**: {len(record.tools)} tools consuming ~{int(total_tool_chars / 4.24):,} tokens\n")
    
    if record.prompt_tokens:
        ratio = (total_chars / 4.24) / record.prompt_tokens * 100 if record.prompt_tokens > 0 else 0
        report.append(f"3. **Token estimation accuracy**: Est ~{int(total_chars / 4.24):,} vs Actual {record.prompt_tokens} ({ratio:.0f}%)\n")
    
    report.append("\n---\n")
    report.append(f"*Report generated by sglang-log-analyze skill*\n")
    
    return "".join(report)


def main():
    parser = argparse.ArgumentParser(description="Analyze SGLang/LLM API request logs")
    parser.add_argument("log_file", help="Path to log file")
    parser.add_argument("--rid", help="Specific request ID to analyze")
    parser.add_argument("--output", "-o", help="Output directory for reports")
    parser.add_argument("--type", help="Filter by request type (agent_request, skill_load, etc.)")
    parser.add_argument("--segment", action="store_true", help="Segment user questions by time gap")
    parser.add_argument("--stats", action="store_true", help="Generate detailed statistics report")
    parser.add_argument("--time-gap", type=float, default=60.0, help="Time gap threshold in seconds (default: 60)")
    
    args = parser.parse_args()
    
    # Handle stats mode
    if args.stats:
        report = generate_detailed_stats_report(args.log_file, args.time_gap)
        print(report)
        
        if args.output:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"detailed_stats_{timestamp}.md"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            
            print(f"\nReport saved to: {output_file}")
        return
    
    # Handle segmentation mode
    if args.segment:
        report = generate_segmentation_report(args.log_file, args.time_gap)
        print(report)
        
        if args.output:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"segmentation_{timestamp}.md"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            
            print(f"\nReport saved to: {output_file}")
        return
    
    records = parse_log_file(args.log_file, args.rid)
    
    if not records:
        print("No matching requests found.")
        return
    
    if args.type:
        records = [r for r in records if r.request_type == args.type]
        if not records:
            print(f"No requests of type '{args.type}' found.")
            return
    
    print(f"Found {len(records)} request(s)\n")
    
    for record in records:
        print("=" * 80)
        print(f"Request: {record.rid}")
        print(f"Type: {record.request_type}")
        print(f"Time: {record.timestamp}")
        print("=" * 80)
        
        report = generate_report(record)
        print(report)
        
        if args.output:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"analysis_{record.rid[:8]}_{timestamp}.md"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            
            print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
