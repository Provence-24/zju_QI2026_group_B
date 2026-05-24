## TODO
`2026-05-11 14:06`<br>
整理各平台的物理特性，比如：门参数、拓扑结构。<br>
（optional）也可以提供一些物理实现上的原理。<br>
p.s. 基本不用看代码<br>

- 为什么需要这些特性？

表面码的逻辑错误率本质上是由底层物理比特的连接性和门保真度决定的。
![](template.png)

请参考 `template.png` 从以下这个框架来给出调研结果（结果写在 `survey` 目录下对应的文件夹中）：

1. 原生门集合与错误率： 单比特门、双比特门（如 CZ, CNOT）的平均保真度。（可根据各平台的物理特性来说明可能的原因）
2. 测量与重置时间： 这一点极其重要，因为表面码需要不断地循环测量 Stabilizers（稳定子）。测量时间过长会导致数据比特发生严重的退相干。
3. 连接性约束限制： 遇到非相邻比特需要交互时，该平台的代价是什么？（是需要引入带噪的 SWAP 门，还是需要物理移动比特？）

# QI2026 Surface Code Study

比较三种量子硬件平台（超导、中性原子、离子阱）上表面码的逻辑错误率，支持多种解码器（MWPM、Union-Find）和两种电路构建方式（stim 内置电路 / 平台感知编译器）。

## 平台

| 平台 | 代表 | 主要噪声源 |
|------|------|-----------|
| 超导 | Google Willow | idle 退相干 |
| 中性原子 | Bluvstein 2024 | 2Q 门错误 |
| 离子阱 | Quantinuum H2 | 测量错误 |

## 快速开始

**安装**（二选一）：

```bash
uv sync            # 方式1：直接安装
.\setup.bat        # 方式2：Windows 一键脚本（含 uv 安装）
./setup.sh         #         Linux/Mac 一键脚本
```

**运行实验**（无需手动激活 venv，`uv run` 自动处理）：

```bash
# stim 内置电路模式（默认）
uv run python -m surface_code_study.experiments.exp1_pl_vs_p
uv run python -m surface_code_study.experiments.exp2_pl_vs_d
uv run python -m surface_code_study.experiments.exp3_platform_compare

# PlatformCompiler 模式（平台感知物理电路）
uv run python -m surface_code_study.experiments.exp3_platform_compare --use_compiler --d 3 5 7
```

**运行测试**：

```bash
uv run pytest surface_code_study/tests/ -v
```

## 依赖

- stim >= 1.11
- pymatching >= 2.0
- numpy, matplotlib, scipy

## 结果

图片和 JSON 保存在 `results/` 目录，按模式分到 `builtin/` 和 `compiler/` 子目录。

实验数据对比见 [results/RESULTS.md](results/RESULTS.md)。

详细说明见 [surface_code_study/README.md](surface_code_study/README.md)。
