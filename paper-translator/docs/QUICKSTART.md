# 论文阅读与翻译工具 - 快速入门

> 使用本工具快速完成论文的PDF提取和翻译工作

---

## ⚡ 5分钟快速开始

### 步骤1: 安装依赖
```bash
pip install pypdf PyMuPDF pillow
```

### 步骤2: 提取PDF文本
```bash
# 基本用法 - 提取前10页
python pdf_reader.py paper.pdf 1 10 -o output.txt

# 提取全部内容
python pdf_reader.py paper.pdf 1 100 -o full.txt
```

### 步骤3: 提取目录（可选）
```bash
python pdf_reader.py paper.pdf --toc
```

### 步骤4: 开始翻译
使用提取的文本进行翻译工作。

---

## 📖 完整功能列表

### 🔤 文本提取

| 命令 | 说明 | 示例 |
|------|------|------|
| `python pdf_reader.py <file> <start> <end>` | 提取指定页面 | `python pdf_reader.py a.pdf 1 10` |
| `-o <file>` | 保存到文件 | `python pdf_reader.py a.pdf 1 10 -o out.txt` |

### 📑 目录提取

| 命令 | 说明 | 示例 |
|------|------|------|
| `--toc` | 提取目录 | `python pdf_reader.py a.pdf --toc` |

### 🖼️ 图片处理

| 命令 | 说明 | 示例 |
|------|------|------|
| `--images <dir>` | 提取所有图片 | `python pdf_reader.py a.pdf --images ./imgs` |
| `--page-image <n> <file>` | 单页转图片 | `python pdf_reader.py a.pdf --page-image 1 page1.png` |
| `--all-images <dir>` | 批量页面转图片 | `python pdf_reader.py a.pdf --all-images ./pages` |

### ❓ 帮助

| 命令 | 说明 |
|------|------|
| `--help` 或 `-h` | 显示帮助信息 |

---

## 💡 使用场景示例

### 场景1: 翻译arXiv论文

```bash
# 1. 下载PDF
# wget https://arxiv.org/pdf/xxxx.pdf

# 2. 查看目录结构
python pdf_reader.py paper.pdf --toc

# 3. 分段提取文本（避免一次性提取过多）
python pdf_reader.py paper.pdf 1 15 -o ch1.txt    # 摘要+引言
python pdf_reader.py paper.pdf 16 30 -o ch2.txt   # 方法
python pdf_reader.py paper.pdf 31 45 -o ch3.txt   # 实验
python pdf_reader.py paper.pdf 46 60 -o ch4.txt   # 结论+附录

# 4. 翻译每部分
# 将文本复制到翻译工具中进行翻译

# 5. 合并翻译内容
```

### 场景2: 提取论文中的图表

```bash
# 提取论文中所有图片
python pdf_reader.py paper.pdf --images ./figures

# 转换特定页面为图片（用于保留复杂公式/图表）
python pdf_reader.py paper.pdf --page-image 5 fig5.png
python pdf_reader.py paper.pdf --page-image 10 fig10.png
```

### 场景3: 创建术语表

```bash
# 1. 提取目录识别关键术语
python pdf_reader.py paper.pdf --toc

# 2. 提取全文
python pdf_reader.py paper.pdf 1 100 -o full.txt

# 3. 使用术语表模板
# 参考 terminology/template.md 创建项目术语表
```

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **分批处理大PDF**
   - 建议每批10-20页
   - 避免内存不足

2. **先提取目录**
   - 了解论文结构
   - 规划翻译顺序

3. **保存中间结果**
   - 每批提取后保存到文件
   - 便于检查和修改

4. **建立术语表**
   - 从摘要和引言开始收集术语
   - 保持全文一致性

### ❌ 避免做法

1. **不要一次性提取100+页**
   - 可能导致超时或内存错误

2. **不要忽视编码问题**
   - Windows系统注意UTF-8

3. **不要跳过目录提取**
   - 目录包含重要结构信息

---

## 🔧 常见问题

### Q: 提取的文本有乱码？
**A:** 可能是PDF扫描件或特殊字体，尝试：
- 使用PDF阅读器打开检查
- 或使用OCR工具处理

### Q: 图片提取失败？
**A:** 确保安装了PyMuPDF：
```bash
pip install PyMuPDF
```

### Q: 内存不足？
**A:** 减少每批提取的页数，或使用：
```bash
# 只提取前5页测试
python pdf_reader.py large.pdf 1 5
```

---

## 📝 翻译工作流

```
┌─────────────┐
│  1. 环境准备  │
└──────┬──────┘
       ▼
┌─────────────┐
│  2. PDF分析  │ ──> 提取目录结构
└──────┬──────┘
       ▼
┌─────────────┐
│  3. 文本提取  │ ──> 分批提取文本
└──────┬──────┘
       ▼
┌─────────────┐
│  4. 术语收集  │ ──> 建立术语表
└──────┬──────┘
       ▼
┌─────────────┐
│  5. 翻译执行  │ ──> 按章节翻译
└──────┬──────┘
       ▼
┌─────────────┐
│  6. 质量检查  │ ──> 术语/格式检查
└──────┬──────┘
       ▼
┌─────────────┐
│  7. 保存发布  │
└─────────────┘
```

---

## 📚 相关文档

- **完整Agent手册**: `AGENTS.md`
- **术语表模板**: `terminology/template.md`
- **项目总结**: `PROJECT_SUMMARY.md`

---

## 🎉 开始使用

现在你已经了解了工具的基本用法，可以开始处理你的论文了！

```bash
# 查看帮助
python pdf_reader.py --help

# 提取你的第一篇论文
python pdf_reader.py your_paper.pdf 1 10 -o output.txt
```

Happy translating! 🚀
