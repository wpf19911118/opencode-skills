---
name: gpu-profiler-generic
description: 通用GPU性能分析工具 - 支持CUDA、AMD、Intel和OMP架构的profiling和报告生成
---

# GPU Profiler Generic - SKILL

> 通用GPU性能分析工具

## 📋 描述

本SKILL提供GPU性能分析功能，支持多种GPU架构的profiling和报告生成。

### 支持的架构
- CUDA (NVIDIA)
- AMD GPU
- Intel GPU
- OpenMP (OMP)

### 功能特性
- 内置MPI支持
- 内核调优
- IO监控
- 功耗监控
- 性能profiling
- API错误捕获

---

## 🛠️ 环境要求

### 依赖项
- Python 3.x
- CUDA Toolkit (如使用NVIDIA GPU)
- 相关GPU驱动

### 安装
```bash
# 克隆仓库
git clone https://github.com/hongyan19890126/gpu-profiler-generic.git
cd gpu-profiler-generic

# 运行报告生成
python generate_report.py
```

---

## 📁 文件结构

```
gpu-profiler-generic/
├── SKILL.md              # 本文件
├── README.md             # 项目说明
└── generate_report.py    # 报告生成脚本
```

---

## 🚀 使用方法

### 1. 基本使用

```bash
# 运行性能分析
python generate_report.py
```

### 2. 生成报告

报告将包含：
- GPU利用率统计
- 内存使用情况
- 功耗数据
- 内核执行时间
- 性能瓶颈分析

---

## 📚 相关资源

- **GitHub仓库**: https://github.com/hongyan19890126/gpu-profiler-generic
- **作者**: hongyan19890126

---

## 🔧 配置

根据你的GPU架构，可能需要配置以下环境变量：

```bash
# CUDA配置
export CUDA_HOME=/usr/local/cuda

# AMD ROCm配置
export ROCM_HOME=/opt/rocm

# Intel OneAPI配置
export ONEAPI_ROOT=/opt/intel/oneapi
```

---

## ⚠️ 注意事项

1. 确保已安装正确的GPU驱动
2. 根据GPU类型选择合适的profiling工具
3. 查看仓库README获取详细文档

---

**版本**: 1.0.0
**更新日期**: 2026-04-29
