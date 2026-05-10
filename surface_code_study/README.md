# Surface Code Study

**目标**：比较三种量子硬件平台（超导、中性原子、离子阱）上表面码（surface code）的逻辑错误率，支持多种解码器（MWPM、Union-Find 等）。

---

## 运行时间参考

> 在典型笔记本（CPU: Apple M-series 或同级 x86）上，各实验参考运行时间：
>
> | 实验 | 内容 | 预计时间 |
> |---|---|---|
> | exp1 PL vs p | d=5，3平台×10个p点，自适应采样 | ~3 分钟 |
> | exp2 PL vs d | p=0.1%，4个d值×3平台，自适应采样 | ~15 分钟 |
> | exp3 综合对比 | d=3,5,7,9 + d_needed 查找 | ~25 分钟 |

> ⚠️ d>9 的点运行时间急剧增加（电路规模 O(d²)，采样复杂度同步上升）。建议 d 上限设为 9 或 11。

---

## 框架概览

```
surface_code_study/
├── platforms.py          ← 三种平台的噪声参数（附文献引用）
├── circuit_builder.py    ← 用 stim 构建旋转表面码 memory experiment 电路
├── simulator.py         ← 采样 → 解码 → 统计 PL 核心 pipeline
├── experiments/
│   ├── exp1_pl_vs_p.py        ← 实验1：固定 d，扫描 p（PL vs p 曲线）
│   ├── exp2_pl_vs_d.py        ← 实验2：固定 p，扫描 d（验证指数压制）
│   └── exp3_platform_compare.py  ← 实验3：综合对比 + 汇总表
├── analysis/
│   ├── plotting.py       ← matplotlib 绘图工具
│   └── fitting.py        ← 错误压制因子 Λ 拟合
└── tests/
    └── test_sanity.py    ← 基本健康检查
```

---

## 依赖

```
stim >= 1.11
pymatching >= 2.0
numpy
matplotlib
scipy
```

安装：`pip install -e .`（在项目根目录执行）

---

## 快速开始

### 一、验证安装

```bash
python -c "from surface_code_study import platforms, simulator; print('OK')"
```

### 二、跑全部三个实验

```bash
# 实验1：PL vs p（三平台对比，log-log 图）
python -m surface_code_study.experiments.exp1_pl_vs_p

# 实验2：PL vs d（验证指数压制，打印 Λ 值）
python -m surface_code_study.experiments.exp2_pl_vs_d

# 实验3：综合对比 + 汇总表
python -m surface_code_study.experiments.exp3_platform_compare
```

### 三、查看结果

图片和 JSON 数据保存在 `results/` 目录：

```
results/
├── exp1_pl_vs_p.png / pdf   ← PL vs p 对比图
├── exp1_pl_vs_p.json        ← 原始数据
├── exp2_pl_vs_d.png / pdf   ← PL vs d 压制曲线
├── exp2_pl_vs_d.json
├── exp3_platform_compare.png / pdf
└── exp3_platform_compare.json
```

---

## 各实验说明

### 实验1：PL vs p（逻辑错误率 vs 物理错误率）

- **固定参数**：d=5, R=d（5轮）
- **扫描范围**：p ∈ [10⁻⁵, 10⁻³]（对数等距 10 个点）
- **自适应采样**：每个数据点采到 100 个逻辑错误为止（相对误差 ~10%）
- **输出**：log-log 图，三条曲线分别代表超导、中性原子、离子阱

**期望行为**：
- 在阈值以下，PL 随 p 线性增长（斜率 ≈ 1）
- 阈值附近曲线开始上翘（接近 p_th^(d+1)/2 标度）

### 实验2：PL vs d（验证指数压制）

- **固定参数**：p = 0.1%（当前硬件典型水平），R=d
- **扫描范围**：d ∈ {3, 5, 7, 9}
- **输出**：semilogy 图，拟合压制因子 Λ

**物理公式**：

$$P_L \approx \Lambda \cdot p^{(d+1)/2}$$

取对数：

$$\log_{10} P_L \approx \frac{d+1}{2} \log_{10} p + \log_{10} \Lambda$$

斜率固定为 (d+1)/2（与 p 无关），拟合截距给出 Λ。

**期望行为**：
- p < p_threshold 时，d 增大 PL 下降（错误压制）
- p > p_threshold 时，d 增大 PL 上升（阈值以下反而恶化）

### 实验3：综合对比

- 包含实验1和实验2的所有图表
- 额外计算"达到 PL=10⁻⁶ 所需的最小码距 d"
- 生成汇总表

---

## 平台参数来源

| 参数 | 超导 (Willow) | 中性原子 (Bluvstein 2024) | 离子阱 (Quantinuum H2) |
|------|-------------|----------------------|-------------------|
| p₁q | 3×10⁻⁴ | 1×10⁻³ | 1×10⁻⁴ |
| p₂q | 1×10⁻³ | 6×10⁻³ | 1×10⁻³ |
| p_meas | 5×10⁻³ | 5×10⁻³ | 6×10⁻³ |
| p_reset | 1×10⁻⁴ | 5×10⁻³ | 1×10⁻³ |
| p_idle/cycle | 1×10⁻² | 1×10⁻³ | ~10⁻⁶ |
| cycle 时间 | 1 μs | 1 μs | 10 μs |

**文献**：
- 超导：[Google Quantum AI, arXiv:2408.13687 (2024)](https://arxiv.org/abs/2408.13687)
- 中性原子：[Bluvstein et al., Nature 627, 263-269 (2024)](https://arxiv.org/abs/2312.13231)
- 离子阱：Quantinuum H2 Technical Brief (2024-2025)

> 标注"estimate,待校准"的参数需要后续用实际硬件数据修正。

---

## 核心公式

### PL 折算（per logical per cycle）

$$P_L = \frac{1 - (1 - 2 P_{\text{run}})^{1/R}}{2}$$

其中 P_run 是单次实验（d+1 轮）的整体逻辑错误概率，R 是 syndrome 提取轮数。

### 错误压制

$$P_L \approx \Lambda \cdot p^{(d+1)/2}$$

Λ 是错误压制因子，与平台的具体错误通道结构有关。

---

## 在自己的代码中使用

```python
from surface_code_study.circuit_builder import build_surface_code_circuit
from surface_code_study.platforms import get_platform
from surface_code_study.simulator import (
    DEFAULT_DECODER,
    get_decoder,
    run_adaptive_experiment,
)

# 构建电路
platform = get_platform("superconducting")
circuit = build_surface_code_circuit(d=5, platform_params=platform._asdict(), noise_scale=0.1)

# 创建解码器（使用 DEFAULT_DECODER 指定的解码器）
decoder = get_decoder(DEFAULT_DECODER, circuit)

# 运行实验
result = run_adaptive_experiment(
    circuit=circuit, num_rounds=5, d=5,
    decoder=decoder,  # 注意：需要传入 decoder 参数
    platform_name="superconducting", p_scale=0.1,
    min_logical_errors=200,
)

print(f"PL = {result.pl:.3e} ± {result.pl_std:.3e}")
print(f"采样了 {result.num_shots} 次，积累 {result.num_logical_errors} 个逻辑错误")
```

---

## 运行测试

```bash
python -m pytest surface_code_study/tests/test_sanity.py -v
```

测试内容：
1. 零噪声 → PL = 0
2. d=3, p=10% → PL > 10%（明显恶化）
3. p 固定时 d 增大 → PL 下降（仅当 p < threshold）
4. d=3, p=0.1%, 10⁵ 次采样在数秒内完成

---

## 切换解码器

所有实验使用统一的解码器配置，集中管理在 `simulator.py` 中。

**修改位置**：`surface_code_study/simulator.py` 第 217 行

```python
DEFAULT_DECODER: str = "mwpm"
```

**支持的解码器**：

| 名称 | 说明 |
|------|------|
| `"mwpm"` | Minimum Weight Perfect Matching（pymatching，默认） |
| `"uf"` 或 `"unionfind"` | Union-Find 并查集解码器 |

**切换示例**：
```python
# 编辑 simulator.py，将 DEFAULT_DECODER 改为：
DEFAULT_DECODER: str = "uf"
```

**在自己的代码中使用指定解码器**：
```python
from surface_code_study.simulator import get_decoder, DEFAULT_DECODER

decoder = get_decoder(DEFAULT_DECODER, circuit)
result = run_single_experiment(..., decoder=decoder, ...)
```

**添加新的解码器**：
1. 在 `simulator.py` 中实现继承自 `Decoder` 的新类
2. 在 `get_decoder()` 函数中注册新的解码器名称

---

## 常见问题

**Q: p 已经很小了但 PL 还是很低？**
A: d=5 时需要 p 低于阈值（约 1%）才能观察到明显压制。如果 p_scale=0.001（0.1%）在阈值以下，PL 应该随 d 增大而下降。

**Q: 采样太慢怎么办？**
A: 减少 `min_logical_errors`（默认100），或限制 `max_shots`。对于快速测试可用 `run_single_experiment(..., num_shots=1000)`。

**Q: 可以修改某个平台的参数吗？**
A: 直接编辑 `platforms.py` 中对应平台的返回值。所有实验基于该文件中的参数。

---

## 研究结果摘要

> 以下数据来自模拟结果（stim + pymatching MWPM 解码，旋转表面码，R=d）。

### 1. 平台自然工作点下的 PL（d=5, noise_scale=1.0）

| 平台 | PL（d=5, natural） | 主要噪声源 |
|---|---|---|
| 离子阱 | ~5×10⁻⁵ | 测量错误（0.6%）|
| 超导 | ~4.6×10⁻⁴ | idle 退相干（1%/cycle）|
| 中性原子 | ~1.8×10⁻³ | 2Q 门错误（0.6%）|

### 2. 达到 PL=10⁻⁶ 所需的最小码距（p=0.1% 2Q门错误）

| 平台 | 所需最小 d | 备注 |
|---|---|---|
| 中性原子 | **d=7** | 压制因子最强（Λ 最小）|
| 离子阱 | **d=9** | 测量错误高但门错误极低 |
| 超导 | **d=15** | idle 退相干（1%/cycle）限制压制效率 |

### 3. 关键物理发现

- **中性原子压制效率最高**：d=7 时 PL≈1.4×10⁻⁷（p=0.1%）。Rydberg 门的高错误率（0.6%）在错误纠正中被有效压制，idle 错误低（0.1%/cycle）也有贡献。
- **离子阱 PL 最低**：在相同 p₂q=0.1% 下，离子阱的 p_idle≈10⁻⁶ 使其成为 idle 错误主导场景下的最优选择。
- **超导主要受限**：idle 退相干（1%/cycle）是主要瓶颈，而非 2Q 门错误。这与 Google Willow 论文中报告的 T2~100μs 一致。

### 4. 图片文件

所有图片保存在 `results/` 目录：
- `exp1_pl_vs_p.png/pdf` — PL vs noise_scale（d=5）
- `exp2_pl_vs_d.png/pdf` — PL vs d（p=0.1% 2Q门错误）
- `exp3_platform_compare.png/pdf` — 综合对比图
