# Surface Code Study

**目标**：比较三种量子硬件平台（超导、中性原子、离子阱）上表面码（surface code）的逻辑错误率，支持多种解码器（MWPM、Union-Find）和两种电路构建方式（stim 内置电路 / 平台感知编译器）。

---

## 运行时间参考

> 在典型笔记本（CPU: Apple M-series 或同级 x86）上，各实验参考运行时间：
>
> | 实验 | 内容 | builtin | compiler |
> |---|---|---|---|
> | exp1 PL vs p | d=5，3平台×10个p点，自适应采样 | ~2 分钟 | ~5 秒 |
> | exp2 PL vs d | p=0.1%，4个d值×3平台，自适应采样 | ~16 分钟 | ~5 秒 |
> | exp3 综合对比 | d=3,5,7,9 + d_needed 查找 | ~25 分钟 | ~15 秒 |

> ⚠️ d>9 的点运行时间急剧增加（电路规模 O(d²)，采样复杂度同步上升）。建议 d 上限设为 9 或 11。
>
> ⚠️ builtin 模式在低 PL 时需要大量采样（如中性原子 d=9 时 PL~10⁻⁸，需 10⁷ shots），运行时间主要由低 PL 数据点决定。compiler 模式在自然噪声下 PL 较高（~10⁻³），自适应采样快速收敛；但若降低噪声使 PL 降至 10⁻⁵ 以下，compiler 的单 shot 开销（显式 gate + idle noise 指令）更大，运行时间会反超 builtin。

---

## 框架概览

```
surface_code_study/
├── platforms.py            ← 三种平台的噪声参数（附文献引用 + T1/T2）
├── circuit_builder.py      ← 用 stim 构建旋转表面码 memory experiment 电路
├── simulator.py            ← 采样 → 解码 → 统计 PL 核心 pipeline
│                            （内置 MWPM 和 Union-Find 两种解码器）
├── compilers/              ← 平台感知电路编译器（v2.0 新增）
│   ├── base.py             ← PlatformCompiler 抽象基类
│   ├── superconducting.py  ← 超导编译器（4步CZ调度 + 门噪声）
│   ├── neutral_atom.py     ← 中性原子编译器（区域移动 + 空闲退相干）
│   ├── trapped_ion.py      ← 离子阱编译器（传输噪声 + MS门近似）
│   └── __init__.py         ← get_compiler() 工厂函数
├── experiments/
│   ├── exp1_pl_vs_p.py           ← 实验1：固定 d，扫描 p（PL vs p 曲线）
│   ├── exp2_pl_vs_d.py           ← 实验2：固定 p，扫描 d（验证指数压制）
│   └── exp3_platform_compare.py  ← 实验3：综合对比 + 汇总表
├── analysis/
│   ├── plotting.py         ← matplotlib 绘图工具
│   └── fitting.py          ← 错误压制因子 Λ 拟合
└── tests/
    ├── test_sanity.py      ← 基本健康检查
    └── test_compilers.py   ← 编译器测试（零噪声 + 结构 + DEM 验证）
```

---

## 依赖

```
stim >= 1.11
pymatching >= 2.0
numpy
matplotlib
scipy
pytest (测试用)
```

安装：`uv sync`（在项目根目录执行）

---

## 快速开始

### 一、验证安装

```bash
uv run python -c "from surface_code_study import platforms, simulator; print('OK')"
```

### 二、跑全部三个实验

#### 默认模式（stim 内置电路）

```bash
# 实验1：PL vs p（三平台对比，log-log 图）
uv run python -m surface_code_study.experiments.exp1_pl_vs_p

# 实验2：PL vs d（验证指数压制，打印 Λ 值）
uv run python -m surface_code_study.experiments.exp2_pl_vs_d

# 实验3：综合对比 + 汇总表
uv run python -m surface_code_study.experiments.exp3_platform_compare
```

#### 编译器模式（平台感知物理电路）

```bash
# 实验1：使用编译器构建平台特定电路
uv run python -m surface_code_study.experiments.exp1_pl_vs_p --use_compiler

# 实验2：使用编译器 + 自定义码距
uv run python -m surface_code_study.experiments.exp2_pl_vs_d --use_compiler

# 实验3：快速验证（小码距）
uv run python -m surface_code_study.experiments.exp3_platform_compare --use_compiler --d 3 --rounds 3
```

### 三、查看结果

图片和 JSON 数据保存在 `results/` 目录，按模式自动分到子目录：

```
results/
├── builtin/                        ← stim 内置电路模式
│   ├── exp1_pl_vs_p.png / pdf      ← PL vs p 对比图
│   ├── exp1_pl_vs_p.json           ← 原始数据
│   ├── exp2_pl_vs_d.png / pdf      ← PL vs d 压制曲线
│   ├── exp2_pl_vs_d.json
│   ├── exp3_platform_compare.png / pdf
│   └── exp3_platform_compare.json
└── compiler/                       ← PlatformCompiler 模式
    ├── exp1_pl_vs_p.png / pdf
    ├── exp1_pl_vs_p.json
    ├── exp2_pl_vs_d.png / pdf
    ├── exp2_pl_vs_d.json
    ├── exp3_platform_compare.png / pdf
    └── exp3_platform_compare.json
```

---

## PlatformCompiler 抽象层（v2.0）

平台感知编译器将抽象的表面码电路映射到具体物理平台的 gate sequence，反映真实的物理约束：

| 平台 | 关键物理特征 | 主要噪声机制 |
|------|------------|------------|
| 超导 | 固定晶格，4步CZ调度 | 门噪声 + 短T1/T2退相干 |
| 中性原子 | 区域移动，按方向批量并行 | 移动空闲退相干 + Rydberg门噪声 |
| 离子阱 | ancilla-data 分区，逐对传输 | 传输退相干（ms级）+ 门噪声 |

**两种电路构建方式**：
- `stim 内置`（默认）—— 使用 stim 的 `rotated_surface_code` 生成，噪声模型简化
- `PlatformCompiler`（`--use_compiler`）—— 平台特定 gate sequence，包含移动/传输/空闲退相干

```python
from surface_code_study.compilers import get_compiler

compiler = get_compiler("ion_trap", distance=5, noise_params=params)
circuit = compiler.build_memory_circuit(num_rounds=5)
```

---

## 各实验说明

### 实验1：PL vs p（逻辑错误率 vs 物理错误率）

- **固定参数**：d=5, R=d（5轮）
- **扫描范围**：noise_scale ∈ [0.3, 3.0]（10个对数等距点）
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

- PL vs d 扫描（各平台自然噪声水平下）
- 额外计算"达到 PL=10⁻⁶ 所需的最小码距 d"（p=0.1% 2Q门错误率下扫描 d=3~19）
- 生成汇总表

**命令行参数**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--use_compiler` | 使用平台编译器 | False |
| `--d 3 5 7 9` | 码距列表 | 3,5,7,9 |
| `--rounds N` | 轮数（默认 = d） | None |

---

## 平台参数来源

| 参数 | 超导 (Willow) | 中性原子 (Bluvstein 2024) | 离子阱 (Quantinuum H2) |
|------|-------------|----------------------|-------------------|
| p₁q | 3×10⁻⁴ | 1×10⁻³ | 1×10⁻⁴ |
| p₂q | 1×10⁻³ | 6×10⁻³ | 1×10⁻³ |
| p_meas | 5×10⁻³ | 5×10⁻³ | 6×10⁻³ |
| p_reset | 1×10⁻⁴ | 5×10⁻³ | 1×10⁻³ |
| p_idle/cycle | 1×10⁻² | 1×10⁻³ | ~10⁻⁶ |
| T1 | 100 μs | 1 s | >10 s |
| T2 | 100 μs | 1 ms | >10 s |
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

# 构建电路（stim 内置模式）
platform = get_platform("superconducting")
circuit = build_surface_code_circuit(d=5, platform_params=platform._asdict(), noise_scale=0.1)

# 创建解码器（使用 DEFAULT_DECODER 指定的解码器）
decoder = get_decoder(DEFAULT_DECODER, circuit)

# 运行实验
result = run_adaptive_experiment(
    circuit=circuit, num_rounds=5, d=5,
    decoder=decoder,
    platform_name="superconducting", p_scale=0.1,
    min_logical_errors=200,
)

print(f"PL = {result.pl:.3e} ± {result.pl_std:.3e}")
print(f"采样了 {result.num_shots} 次，积累 {result.num_logical_errors} 个逻辑错误")
```

使用编译器模式：

```python
from surface_code_study.compilers import get_compiler

params = platform._asdict()
compiler = get_compiler("superconducting", distance=5, noise_params=params)
circuit = compiler.build_memory_circuit(num_rounds=5)
# 后续与上例相同
```

---

## 运行测试

```bash
# 基本健康检查
uv run pytest surface_code_study/tests/test_sanity.py -v

# 编译器测试（零噪声 + 结构验证 + DEM）
uv run pytest surface_code_study/tests/test_compilers.py -v

# 全部测试
uv run pytest surface_code_study/tests/ -v
```

**test_sanity.py 测试内容**：
1. 零噪声 → PL = 0
2. d=3, p=10% → PL > 10%（明显恶化）
3. p 固定时 d 增大 → PL 下降（仅当 p < threshold）
4. d=3, p=0.1%, 10⁵ 次采样在数秒内完成

**test_compilers.py 测试内容**：
1. 零噪声 × 3 平台 → PL = 0
2. 电路结构验证 → 含 DETECTOR、OBSERVABLE_INCLUDE
3. 噪声 quorum → 有噪声时 PL > 0 但 < 0.5
4. Qubit 数量 → d=3 预期 17，d=5 预期 49
5. Detector 数量 → 含首轮特殊逻辑
6. DEM 有效性 → decompose_errors 后可构建

---

## 切换解码器

所有实验使用统一的解码器配置，集中管理在 `simulator.py` 中。

**修改位置**：`surface_code_study/simulator.py` 第 332 行

```python
DEFAULT_DECODER: str = "mwpm"
```

**支持的解码器**：

| 名称 | 说明 |
|------|------|
| `"mwpm"` | Minimum Weight Perfect Matching（pymatching，默认） |
| `"uf"` 或 `"unionfind"` | Union-Find 并查集解码器（簇生长算法） |

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

## 如何完整跑测试实验

### 第一步：验证环境

```bash
# 确认依赖安装完整
uv sync

# 运行单元测试确认一切正常
uv run pytest surface_code_study/tests/ -v
```

> 预期：全部 13+ 测试通过（test_sanity.py 4个 + test_compilers.py 9个）

### 第二步：快速冒烟测试（编译器模式）

```bash
# 用小码距快速验证三种编译器都能正常工作
uv run python -m surface_code_study.experiments.exp3_platform_compare --use_compiler --d 3 --rounds 3
```

### 第三步：完整实验运行

```bash
# 实验1：PL vs p（默认 stim 模式，~2分钟）
uv run python -m surface_code_study.experiments.exp1_pl_vs_p

# 实验1：编译器模式（~5秒，PL高时采样少）
uv run python -m surface_code_study.experiments.exp1_pl_vs_p --use_compiler

# 实验2：PL vs d（默认 stim 模式，~16分钟）
uv run python -m surface_code_study.experiments.exp2_pl_vs_d

# 实验2：编译器模式（~5秒，PL不随d衰减）
uv run python -m surface_code_study.experiments.exp2_pl_vs_d --use_compiler

# 实验3：综合对比（默认 stim 模式，~25分钟）
uv run python -m surface_code_study.experiments.exp3_platform_compare

# 实验3：编译器模式（~15秒）
uv run python -m surface_code_study.experiments.exp3_platform_compare --use_compiler
```

### 第四步：对比两种模式的结果

```bash
# 分别跑默认模式和编译器模式，结果会自动保存到不同子目录
uv run python -m surface_code_study.experiments.exp3_platform_compare --d 3 5 7
# → 结果在 results/builtin/exp3_platform_compare.json

uv run python -m surface_code_study.experiments.exp3_platform_compare --use_compiler --d 3 5 7
# → 结果在 results/compiler/exp3_platform_compare.json
```

### 第五步：切换解码器对比

```bash
# 编辑 simulator.py 第 332 行，将 "mwpm" 改为 "uf"
# 然后重新跑实验，观察 MWPM vs Union-Find 的差异
uv run python -m surface_code_study.experiments.exp3_platform_compare --d 3 5 --rounds 3
```

---

## 常见问题

**Q: p 已经很小了但 PL 还是很低？**
A: d=5 时需要 p 低于阈值（约 1%）才能观察到明显压制。如果 p_scale=0.001（0.1%）在阈值以下，PL 应该随 d 增大而下降。

**Q: 采样太慢怎么办？**
A: 减少 `min_logical_errors`（默认100），或限制 `max_shots`。对于快速测试可用 `--d 3 --rounds 3`。

**Q: 可以修改某个平台的参数吗？**
A: 直接编辑 `platforms.py` 中对应平台的返回值。所有实验基于该文件中的参数。

**Q: stim 内置电路和 PlatformCompiler 有什么区别？**
A: stim 内置电路使用简化的 pauli channel 噪声模型；PlatformCompiler 模拟真实物理操作流程（如离子传输、原子移动），噪声来自 T1/T2 退相干计算，更贴近实际硬件。

**Q: 编译器模式为什么有时快有时慢？**
A: 取决于 PL 水平。编译器显式生成每个 gate 和 noise channel（如 PAULI_CHANNEL_1），单 shot 开销更大；但在自然噪声下 idle 退相干使 PL 保持在 ~10⁻³，仅需 1 万 shots 即达标，总时间反而更短。若降低噪声使 PL < 10⁻⁵，则需大量采样，编译器模式会明显慢于 builtin。

---

## 研究结果摘要

> 以下数据来自模拟结果（stim 内置电路 + pymatching MWPM 解码，旋转表面码，R=d）。编译器模式下的结果见 `results/compiler/`。

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

所有图片保存在 `results/` 目录，按模式分到 `builtin/` 和 `compiler/` 子目录：
- `exp1_pl_vs_p.png/pdf` — PL vs noise_scale（d=5）
- `exp2_pl_vs_d.png/pdf` — PL vs d（p=0.1% 2Q门错误）
- `exp3_platform_compare.png/pdf` — 综合对比图
