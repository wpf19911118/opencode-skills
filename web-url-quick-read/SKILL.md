---
name: web-url-quick-read
description: "网页链接快速阅读与分析技能。自动识别网页内容语言（中文/英文），英文内容完整翻译成中文并进行核心点总结，中文内容直接进行核心点总结。适用于快速理解网页文章、论文和文档的主要内容。触发关键词：总结、翻译、摘要、quick read、summary、translate、TLDR、核心要点、主要观点。"
argument-hint: "[URL或文件路径]"
allowed-tools: Read, Write, Glob, Grep, Bash, WebFetch
---

# Web URL Quick Read

快速识别网页内容语言并生成精准总结。英文内容先完整翻译再总结，中文内容直接总结核心要点。

## Quick Start

```
/web-url-quick-read https://example.com/article
/web-url-quick-read ~/Documents/paper.pdf
```

## Core Workflow

### 1. Fetch Content

Use WebFetch with appropriate format:
- **Web articles**: Use markdown format for clean extraction
- **Documents**: Use text format
- **PDFs**: Read tool handles natively

If content is too long (>50KB), summarize progressively in sections.

### 2. Language Detection

First detect the language of the fetched content:
- Check if content contains predominantly Chinese characters (>30% of text)
- If majority Chinese → Chinese mode
- If majority English → English mode

### 3. Processing Mode

#### English Mode (翻译 + 总结)
1. **Full Translation**: Translate entire article content to Chinese
2. **Core Summary**: Apply Analysis Pattern to translated content

#### Chinese Mode (直接总结)
1. **Core Summary**: Apply Analysis Pattern directly to original content

### 4. Analysis Pattern

Extract these elements systematically:

```
## 标题
[Original title or generated Chinese title]

## 核心人物/来源
[Key figures, authors, or sources mentioned]

## 核心概念
1. [Concept 1 - one line]
2. [Concept 2 - one line]
3. [Concept 3 - one line]

## 关键数据/事实
- [Data point 1 with context]
- [Data point 2]

## 主要论点/观点
[2-3 sentences capturing the main argument]

## 核心结论
[One clear conclusion]

## 一句话总结
[One punch line, max 30 words]
```

### 5. Quality Gates

**Must include:**
- At least 3 core concepts
- Source attribution if academic
- Actionable insight or key takeaway
- For English content: Complete translation before summarization

**Skip:**
- Author bio unless relevant
- Irrelevant tangents
- Marketing fluff

## Gotchas

1. **Don't dump full article** — Extract and translate, don't reformat. If user sees walls of text, you've failed.

2. **WebFetch truncation** — Use offset/limit to fetch sections for long articles. Check if content was cut off.

3. **Paywall content** — If fetch fails or shows paywall, inform user and suggest alternative sources.

4. **Non-text content** — Images/videos need description. For PDFs, try Read tool first.

5. **Accurate translation** — For English content, ensure complete and accurate translation before summarizing.

## Progressive Disclosure

For quick requests (e.g., "what's this about"):
- Return only: Title + 3 core concepts + 1 sentence summary

For detailed requests (e.g., "thorough analysis"):
- Return full structured analysis with translation (if English)

Default to concise unless user asks for depth.

## Examples

**English article quick summary:**
> **Title**: The Future of AI Programming
> **Core**: AI自动编程、代码生成效率、人机协作
> **Summary**: AI编程时代已来，未来代码趋近于零，领域知识为王。

**Chinese article quick summary:**
> **Title**: 印刷机时刻：软件业的去神圣化
> **Core**: Loop自动化、AI自噬代码量、人机协作新范式
> **Summary**: AI编程时代已来，未来代码趋近于零，领域知识为王。

**Detailed analysis:**
Full structured output per Analysis Pattern section.
