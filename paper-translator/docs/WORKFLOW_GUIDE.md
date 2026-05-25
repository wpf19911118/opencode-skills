# 📊 论文翻译工作流 - 完整指南

> 本文档提供了从PDF论文到完整翻译的端到端工作流

---

## 🎯 概览

本指南将帮助你完成以下工作：

```
论文PDF ──┬──> 文本提取 ──> 内容整理 ──> 术语收集 ──> 翻译执行 ──> 质量检查 ──> 最终版本
          │
          ├──> 目录提取 ──> 结构识别 ──> 章节规划
          │
          └──> 图片提取 ──> 图表保存 ──> 格式保留
```

---

## 📋 阶段1: 准备工作

### 1.1 环境检查

```bash
# 检查Python版本
python --version
# 确保 >= 3.8

# 检查pip
pip --version
```

### 1.2 安装依赖

```bash
# 一键安装所有依赖
pip install pypdf PyMuPDF pillow

# 验证安装
python -c "import pypdf; import fitz; import PIL; print('All packages installed!')"
```

### 1.3 项目结构

```bash
# 创建项目目录
mkdir translation_project
cd translation_project

# 创建子目录
mkdir -p raw_text terminology translations pdf_images
```

---

## 📄 阶段2: PDF分析

### 2.1 目录提取（推荐第一步）

```bash
# 提取论文目录
python pdf_reader.py paper.pdf --toc

# 示例输出:
# ============================================================
# TABLE OF CONTENTS
# ============================================================
# 1. Introduction ... Page 4
# 2. Architecture ... Page 6
#   2.1 Background ... Page 7
#   2.2 Method ... Page 9
# 3. Experiments ... Page 20
# 4. Conclusion ... Page 30
```

**为什么重要**:
- ✅ 了解论文整体结构
- ✅ 规划翻译顺序
- ✅ 识别关键章节

### 2.2 文本提取

#### 方法1: 分批提取（推荐）

```bash
# 批次1: 摘要和引言 (1-15页)
python pdf_reader.py paper.pdf 1 15 -o raw_text/part1_intro.txt

# 批次2: 方法部分 (16-35页)
python pdf_reader.py paper.pdf 16 35 -o raw_text/part2_method.txt

# 批次3: 实验部分 (36-50页)
python pdf_reader.py paper.pdf 36 50 -o raw_text/part3_experiment.txt

# 批次4: 结论和附录 (51-60页)
python pdf_reader.py paper.pdf 51 60 -o raw_text/part4_conclusion.txt
```

#### 方法2: 一次性提取

```bash
# 适合较短的论文 (< 30页)
python pdf_reader.py paper.pdf 1 30 -o raw_text/full.txt
```

### 2.3 图片提取

#### 提取所有嵌入图片

```bash
python pdf_reader.py paper.pdf --images ./pdf_images

# 输出示例:
# [OK] Saved: ./pdf_images/page5_img1.png
# [OK] Saved: ./pdf_images/page5_img2.png
# ...
```

#### 转换特定页面为图片

```bash
# 保留重要的公式/图表页面
python pdf_reader.py paper.pdf --page-image 5 fig5.png
python pdf_reader.py paper.pdf --page-image 12 fig12.png
python pdf_reader.py paper.pdf --page-image 25 fig25.png
```

#### 批量转换所有页面

```bash
# 将所有页面转换为高清图片
python pdf_reader.py paper.pdf --all-images ./pdf_images/pages
```

---

## 🔤 阶段3: 术语收集

### 3.1 识别核心术语

阅读以下部分识别术语：
1. **摘要** - 核心概念术语
2. **引言** - 领域专用术语
3. **方法** - 技术术语
4. **实验** - 评估指标术语

### 3.2 创建术语表

复制模板文件并填充：

```bash
cp terminology/template.md terminology/[paper_name]_terminology.md
```

### 3.3 术语分类

建议分类方式：

| 类别 | 示例 |
|------|------|
| 核心概念 | Neural Network, Attention, Transformer |
| 架构设计 | Encoder, Decoder, Embedding |
| 训练优化 | Backpropagation, Gradient Descent, Loss |
| 评估指标 | Accuracy, Precision, Recall, F1 |
| 领域术语 | (根据具体论文) |

---

## ✍️ 阶段4: 翻译执行

### 4.1 翻译规划

根据目录结构规划翻译：

```
论文结构:
├── 摘要 (Abstract)
├── 引言 (Introduction)
├── 相关工作 (Related Work)
├── 方法 (Method)
├── 实验 (Experiment)
├── 结论 (Conclusion)
└── 附录 (Appendix)

翻译顺序:
1. 摘要 - 最先翻译，理解核心贡献
2. 引言 - 理解动机和背景
3. 方法 - 技术细节，需要准确
4. 实验 - 结果描述，相对机械
5. 结论 - 总结收尾
6. 附录 - 参考补充材料
```

### 4.2 翻译模板

使用 `AGENTS.md` 中提供的模板：

#### 中文翻译开头

```markdown
# [论文标题]

**作者**: [Authors]
**机构**: [Institution]
**日期**: [Date]

## 摘要

[翻译内容]
```

#### 章节标题

```markdown
## 1. 引言

[内容]

## 2. 相关工作

[内容]

[以此类推]
```

### 4.3 翻译技巧

#### ✅ 推荐做法

1. **保持术语一致**
   - 首次出现时标记英文原文
   - 全文使用相同译法

2. **保留公式格式**
   - LaTeX公式原样保留
   - 数学符号不翻译

3. **图表引用**
   - 保持"图1"、"表1"编号
   - 图表标题准确翻译

4. **代码保留**
   - 代码块原样保留
   - 注释可选择性翻译

#### ❌ 避免做法

1. **机械翻译**
   - 注意中英文语序差异
   - 调整句子结构

2. **过度意译**
   - 技术术语保持准确
   - 避免文学化表达

3. **信息丢失**
   - 检查是否遗漏内容
   - 验证公式完整性

---

## ✅ 阶段5: 质量检查

### 5.1 完整性检查

使用 `AGENTS.md` 中的检查清单：

- [ ] 摘要完整翻译
- [ ] 所有章节已翻译
- [ ] 目录结构完整
- [ ] 附录已包含（如有）
- [ ] 参考文献保留原格式

### 5.2 术语一致性检查

```bash
# 在翻译文档中搜索关键术语
grep -n "神经网络" translated.md  # 检查中文
grep -n "Neural Network" translated.md  # 检查英文
```

确保：
- ✅ 同一术语译法一致
- ✅ 公式变量命名统一
- ✅ 图表标题术语一致

### 5.3 格式检查

- [ ] 标题层级正确（#, ##, ###）
- [ ] 列表格式统一
- [ ] 代码块正确标记（```）
- [ ] 公式块正确标记（$$ 或 ```math）
- [ ] 图片路径正确

### 5.4 语言质量

- [ ] 语句通顺自然
- [ ] 无明显机械翻译痕迹
- [ ] 专业术语准确
- [ ] 符合中文学术写作习惯

---

## 💾 阶段6: 保存发布

### 6.1 命名规范

```
[论文名称]_[语言].md

示例:
- deepseek_v4_cn.md (中文翻译)
- deepseek_v4_en.md (英文版本)
- deepseek_v4_jp.md (日文翻译)
```

### 6.2 项目组织

```
translation_project/
├── raw_text/              # 原始提取文本
│   ├── part1.txt
│   ├── part2.txt
│   └── ...
├── terminology/           # 术语表
│   └── paper_terminology.md
├── translations/          # 翻译版本
│   └── paper_cn.md
├── pdf_images/            # 提取的图片
│   └── fig1.png
└── translated_paper.md    # 最终版本
```

### 6.3 备份建议

```bash
# 创建备份
cp translated_paper.md translated_paper_backup.md

# 压缩项目
zip -r translation_project.zip translation_project/
```

---

## 🎓 阶段7: 后续学习

### 7.1 深化理解

- 阅读相关论文
- 复现论文方法
- 撰写阅读笔记

### 7.2 扩展应用

- 制作论文讲解视频
- 撰写技术博客
- 分享翻译成果

### 7.3 持续改进

- 收集反馈意见
- 改进翻译质量
- 更新术语表

---

## 📚 工具参考

### pdf_reader.py 命令速查

| 命令 | 功能 |
|------|------|
| `python pdf_reader.py <file> 1 10` | 提取1-10页 |
| `python pdf_reader.py <file> --toc` | 提取目录 |
| `python pdf_reader.py <file> --images ./dir` | 提取图片 |
| `python pdf_reader.py <file> --page-image <n> out.png` | 单页转图 |
| `python pdf_reader.py <file> --all-images ./dir` | 批量转图 |

### AGENTS.md 章节导航

| 章节 | 内容 |
|------|------|
| 环境要求 | Python和依赖安装 |
| 标准工作流 | 完整翻译流程 |
| pdf_reader工具 | 工具详细用法 |
| 多语言模板 | 中/英/日翻译模板 |
| 术语对照表 | 专业术语参考 |
| 质量检查清单 | 翻译检查项 |
| 故障排除 | 常见问题解决 |

---

## 🎉 成功完成

恭喜！你已完成论文翻译工作流的所有阶段。

### 检查清单

- [x] 环境准备完成
- [x] PDF分析完成
- [x] 术语收集完成
- [x] 翻译执行完成
- [x] 质量检查完成
- [x] 保存发布完成

### 文档清单

- [x] 原始文本提取
- [x] 术语表建立
- [x] 完整翻译版本
- [x] 项目文档齐全

---

## 🚀 下一步

1. **分享成果**
   - 发布到博客/社交媒体
   - 分享给研究伙伴

2. **持续学习**
   - 阅读更多论文
   - 提升翻译技能

3. **工具优化**
   - 反馈使用体验
   - 建议功能改进

---

**祝翻译顺利！** 📚✨
