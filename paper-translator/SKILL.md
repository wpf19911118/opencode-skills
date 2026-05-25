---
name: paper-translator
description: AI驱动的学术论文阅读与翻译系统 - PDF文本提取、目录识别、多语言翻译
---

# Agent: 论文阅读与翻译助手

## 📋 功能描述

本Agent专门用于帮助用户高效阅读和翻译学术论文（PDF格式），提供从文本提取到多语言翻译的完整工作流。

### 核心能力
- 📄 **PDF文本提取** - 分页读取PDF内容，支持大批量处理
- 📑 **目录自动识别** - 智能提取论文目录结构
- 🖼️ **图表提取** - 提取PDF中的图片和将页面转换为图片
- 🔤 **多语言翻译** - 支持中英日韩等多种语言的论文翻译
- 📝 **格式保留** - 保留公式、表格、图表引用等学术格式

---

## 🛠️ 环境要求

### 必需环境
- **Python**: 3.8+
- **操作系统**: Windows / macOS / Linux

### 依赖库
```bash
pip install pypdf PyMuPDF pillow
```

### 快速安装
```bash
pip install pypdf PyMuPDF pillow
```

---

## 📁 文件结构

```
项目目录/
├── pdf_reader.py           # PDF处理核心工具
├── AGENTS.md               # 本文档
├── terminology/            # 术语对照表目录
│   └── template.md         # 术语表模板
├── translations/           # 翻译输出目录
│   └── [论文名]_cn.md      # 中文翻译
└── pdf_images/             # PDF图片目录
```

---

## 🚀 标准工作流

### 第一阶段：环境准备

```
1. 检查Python环境
   └─ python --version

2. 安装依赖
   └─ pip install pypdf PyMuPDF pillow
```

### 第二阶段：PDF分析

```
1. 创建PDFReader实例
   └─ 使用pdf_reader.py读取PDF

2. 提取目录（可选但推荐）
   └─ python pdf_reader.py paper.pdf --toc

3. 分批提取文本
   └─ 建议每批10-20页，避免超时
```

### 第三阶段：内容整理

```
1. 合并提取的文本
2. 识别论文结构
   └─ 摘要、引言、方法、实验、结论
3. 建立术语表（见附录A）
```

### 第四阶段：翻译执行

```
1. 按章节分块翻译
2. 保留公式和图表引用
3. 保持术语一致性
4. 格式美化
```

### 第五阶段：质量检查

```
1. 完整性检查（见附录B）
2. 术语一致性检查
3. 格式校对
4. 保存最终版本
```

---

## 📖 pdf_reader.py 工具详解

### 基本用法

```bash
# 提取前10页文本
python pdf_reader.py paper.pdf 1 10 -o output.txt

# 提取指定范围
python pdf_reader.py paper.pdf 15 30 -o part2.txt

# 提取全部内容
python pdf_reader.py paper.pdf 1 100 -o full_text.txt
```

### 高级功能

```bash
# 提取目录
python pdf_reader.py paper.pdf --toc

# 提取所有嵌入图片
python pdf_reader.py paper.pdf --images ./images

# 单页转图片
python pdf_reader.py paper.pdf --page-image 1 page1.png

# 全部页面转图片
python pdf_reader.py paper.pdf --all-images ./pdf_pages
```

### Python API

```python
from pdf_reader import PDFReader

# 初始化
reader = PDFReader("paper.pdf")

# 提取目录
toc = reader.extract_toc()

# 提取文本
text = reader.extract_text(1, 10)

# 提取图片
count = reader.extract_images("./images")

# 页面转图片
reader.page_to_image(1, "page1.png")
```

---

## 🌐 多语言翻译模板

### 中文翻译模板

```markdown
# [论文标题]

**作者**: [Authors]
**机构**: [Institution]
**日期**: [Date]

## 摘要

[翻译内容]

## 1. 引言

[翻译内容]

## 2. 相关工作

[翻译内容]

[... 以此类推 ...]

---

## 附录

### A. 术语对照表

| 英文术语 | 中文术语 | 备注 |
|---------|---------|------|
| ... | ... | ... |

### B. 公式说明

[公式解释]

---

*本翻译由AI辅助生成，如有问题请以原文为准。*
```

### 日文翻译模板

```markdown
# [論文タイトル]

**著者**: [Authors]
**所属**: [Institution]
**日付**: [Date]

## あらすじ

[翻訳内容]

## 1. はじめに

[翻訳内容]

[... 以此类推 ...]
```

### 英文翻译模板（用于中译英）

```markdown
# [Chinese Title]

**Authors**: [Authors]
**Institution**: [Institution]
**Date**: [Date]

## Abstract

[Translated content]

## 1. Introduction

[Translated content]

[... etc ...]
```

---

## 📊 论文结构识别指南

### 典型学术论文结构

| 章节 | 内容描述 | 关键词 |
|------|---------|--------|
| Abstract | 研究概述 | Summary, Abstract |
| Introduction | 研究背景和动机 | Introduction, Motivation |
| Related Work | 现有方法和不足 | Related Work, Background |
| Method | 核心方法 | Method, Approach, Proposed |
| Experiment | 实验设置和结果 | Experiment, Evaluation |
| Conclusion | 总结和未来工作 | Conclusion, Summary |

### 快速识别技巧

```
1. 摘要通常在第一页
2. 目录在论文开头
3. 引用文献在最后
4. 图表通常在方法/实验部分
5. 公式在方法部分密集
```

---

## 🔑 学术术语对照表

### AI/ML领域常用术语

| 英文 | 中文 | 日文 | 备注 |
|------|------|------|------|
| Neural Network | 神经网络 | ニューラルネットワーク | |
| Deep Learning | 深度学习 | 深層学習 | |
| Transformer | Transformer | Transformer | 通常不翻译 |
| Attention | 注意力机制 | アテンションメカニズム | |
| Model | 模型 | モデル | |
| Training | 训练 | 学習/訓練 | |
| Inference | 推理/推断 | 推論 | |
| Parameter | 参数 | パラメータ | |
| Layer | 层 | レイヤー | |
| Token | Token/词元 | トークン | |
| Embedding | 嵌入 | 埋め込み | |
| Fine-tuning | 微调 | ファインチューニング | |
| Pre-training | 预训练 | 事前学習 | |
| Gradient | 梯度 | 勾配 | |
| Loss | 损失 | 損失 | |
| Backpropagation | 反向传播 | 誤差逆伝播法 | |
| Optimization | 优化 | 最適化 | |
| Benchmark | 基准 | ベンチマーク | |
| Dataset | 数据集 | データセット | |
| Architecture | 架构 | アーキテクチャ | |

### 计算机视觉术语

| 英文 | 中文 | 日文 |
|------|------|------|
| Object Detection | 目标检测 | 物体検出 |
| Image Segmentation | 图像分割 | 画像セグメンテーション |
| Convolutional | 卷积 | 畳み込み |
| Feature Map | 特征图 | フィーチャーマップ |
| Pooling | 池化 | プーリング |

---

## ✅ 翻译质量检查清单

### 完整性检查
- [ ] 摘要完整翻译
- [ ] 所有章节已翻译
- [ ] 目录结构完整
- [ ] 附录已包含（如有）
- [ ] 参考文献保留原格式

### 准确性检查
- [ ] 核心术语一致
- [ ] 公式正确保留
- [ ] 图表引用完整
- [ ] 数值单位准确
- [ ] 人名/地名规范

### 格式检查
- [ ] 标题层级正确
- [ ] 列表格式统一
- [ ] 代码块正确标记
- [ ] 图片路径正确
- [ ] 链接可访问

### 语言质量检查
- [ ] 语句通顺
- [ ] 无机械翻译痕迹
- [ ] 专业术语准确
- [ ] 符合目标语言习惯

---

## 📝 翻译任务模板

### 任务启动模板

```markdown
## 翻译任务卡

### 基本信息
- **论文标题**: [原文标题]
- **目标语言**: [中文/英文/日文]
- **创建日期**: [YYYY-MM-DD]
- **预计页数**: [X] 页

### 论文概况
- **作者**: [Authors]
- **发表时间**: [Year]
- **领域**: [Domain]
- **关键词**: [Keywords]

### 章节划分
| 章节 | 起止页 | 状态 |
|------|--------|------|
| 摘要 | 1 | [ ] |
| 引言 | 2-5 | [ ] |
| ... | ... | [ ] |

### 术语表
| 英文 | 中文 | 确认 |
|------|------|------|
| | | [ ] |

### 备注
[特殊说明或注意事项]
```

### 进度跟踪模板

```markdown
## 翻译进度

### 总体进度
██████████░░░░░░░░░░░ 50%

### 各章节状态
| 章节 | 翻译 | 校对 | 格式 |
|------|------|------|------|
| 1. 摘要 | ✅ | ✅ | ✅ |
| 2. 引言 | ✅ | ⏳ | ⏳ |
| 3. 方法 | ⏳ | ⏳ | ⏳ |
| 4. 实验 | ⏳ | ⏳ | ⏳ |
| 5. 结论 | ⏳ | ⏳ | ⏳ |

### 待解决问题
- [ ] 问题1
- [ ] 问题2

### 完成日期
预计: [YYYY-MM-DD]
实际: [YYYY-MM-DD]
```

---

## ⚠️ 注意事项

### PDF处理
1. **编码问题**: Windows下确保使用UTF-8编码
2. **大批量处理**: 建议分批处理（每批10-20页）
3. **图片质量**: 使用zoom参数调整输出图片清晰度
4. **复杂公式**: 某些LaTeX公式可能无法完美提取

### 翻译质量
1. **专业审核**: 重要论文建议人工审核
2. **术语一致性**: 同一术语在全文保持一致
3. **上下文理解**: 避免孤立翻译，确保上下文连贯
4. **版权意识**: 仅用于学习和研究目的

### 性能优化
1. **内存管理**: 大PDF分批处理
2. **缓存利用**: 重复使用已提取的文本
3. **并行处理**: 多个小任务可并行执行

---

## 🔧 故障排除

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 编码错误 | Windows默认编码 | 添加 `sys.stdout.reconfigure(encoding='utf-8')` |
| 导入失败 | 缺少PyMuPDF | `pip install PyMuPDF` |
| 文本为空 | PDF扫描件 | 使用OCR工具（如Tesseract） |
| 图片模糊 | zoom太小 | 增加zoom参数值（推荐2.0+） |

### 调试命令

```bash
# 检查Python版本
python --version

# 检查已安装的包
pip list | grep -E "pypdf|PyMuPDF|pillow"

# 测试PDF读取
python -c "from pdf_reader import PDFReader; r = PDFReader('test.pdf'); print(r.total_pages)"
```

---

## 📚 附录

### 附录A：术语表模板

```markdown
# 术语对照表: [论文名称]

## 计算机科学通用

| 英文 | 中文 | 日文 | 英文缩写 | 首次出现位置 |
|------|------|------|---------|-------------|
| algorithm | 算法 | アルゴリズム | - | 第1页 |
| data structure | 数据结构 | データ構造 | - | 第3页 |

## 领域专用

| 英文 | 中文 | 日文 | 定义/解释 |
|------|------|------|----------|
| attention | 注意力机制 | アテンションメカニズム | 使模型能够关注输入的不同部分 |
```

### 附录B：翻译对照记录

```markdown
# 翻译对照记录

## 日期: YYYY-MM-DD
## 译者: [Name]
## 论文: [Title]

### 疑难词汇
| 原文 | 译法 | 理由 | 确认 |
|------|------|------|------|
| fine-grained | 细粒度 | 相对于coarse-grained | ✓ |
| scalability | 可扩展性 | 常用译法 | ✓ |
```

### 附录C：工具脚本

#### 批量翻译脚本示例

```python
#!/usr/bin/env python3
"""Batch translation script for papers"""

import os
import re
from pathlib import Path

# Translation patterns (示例)
TRANSLATIONS = {
    'Abstract': '摘要',
    'Introduction': '引言',
    'Conclusion': '结论',
    'Related Work': '相关工作',
    # ... more patterns
}

def translate_headings(text):
    """Translate common headings."""
    for eng, cn in TRANSLATIONS.items():
        text = text.replace(eng, cn)
    return text

if __name__ == "__main__":
    # Process files
    pass
```

---

## 📞 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | YYYY-MM-DD | 初始版本创建 |
| ... | ... | ... |

---

*本文档由AI辅助生成和维护，最后更新: YYYY-MM-DD*
