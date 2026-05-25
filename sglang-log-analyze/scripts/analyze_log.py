#!/usr/bin/env python3
"""
SGLang Log Analyzer

Analyzes LLM API request logs to extract system prompts and calculate token overhead.

Usage:
    python analyze_log.py <log_file> [--rid <request_id>] [--output <output_dir>]
"""

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


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
    
    args = parser.parse_args()
    
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
