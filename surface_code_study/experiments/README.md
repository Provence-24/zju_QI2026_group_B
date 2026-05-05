# Experiments

本目录包含三个表面码逻辑错误率实验，用于比较超导、中性原子、离子阱三种量子硬件平台的性能。

---

## 实验概览

| 实验 | 脚本 | 固定参数 | 扫描变量 | 研究目的 |
|------|------|----------|----------|----------|
| 实验1 | `exp1_pl_vs_p.py` | d=5 | noise_scale ∈ {0.3 ~ 3.0} | PL 随物理错误率的变化趋势 |
| 实验2 | `exp2_pl_vs_d.py` | p=0.1% | d ∈ {3, 5, 7, 9} | 验证错误指数压制效应 |
| 实验3 | `exp3_platform_compare.py` | — | 综合对比 | 汇总表 + 最小码距计算 |

---

## 实验1：PL vs p（逻辑错误率 vs 物理错误率）

**脚本**: `exp1_pl_vs_p.py`

### 研究问题
固定码距 d=5，扫描不同的噪声缩放因子，观察逻辑错误率如何变化。

### 核心公式
```
P_L ≈ Λ · p^((d+1)/2)
```

在阈值以下（p < p_th），PL 随 p 线性增长（log-log 图中斜率 ≈ 1）。

### 运行
```bash
python -m surface_code_study.experiments.exp1_pl_vs_p
```

### 输出
- `results/exp1_pl_vs_p.json` — 原始数据
- `results/exp1_pl_vs_p.png` — log-log 绘图
- `results/exp1_pl_vs_p.pdf` — 矢量图

### 调用流程
```
exp1_pl_vs_p.py
    │
    ├── platforms.py        PLATFORMS 字典 → 获取三个平台的噪声参数
    ├── circuit_builder.py  build_surface_code_circuit() → 构建带噪声的 stim 电路
    └── simulator.py
            SimulationResult  (数据类)
            run_adaptive_experiment()  ← 核心调用
```

### 关键代码
```python
# 固定 d=5，扫描 noise_scale
circuit = build_surface_code_circuit(
    d=5,
    platform_params=platform_params,
    rounds=5,
    noise_scale=p,        # 变化的参数
)

result = run_adaptive_experiment(
    circuit=circuit,
    num_rounds=5,
    d=5,
    platform_name=platform_name,
    p_scale=p,
    min_logical_errors=100,  # 自适应采样目标
)
```

---

## 实验2：PL vs d（逻辑错误率 vs 码距）

**脚本**: `exp2_pl_vs_d.py`

### 研究问题
固定物理错误率 p=0.1%，扫描不同码距 d，验证纠错码的指数压制能力。

### 核心公式
```
P_L ≈ Λ · p^((d+1)/2)

取对数：log₁₀(P_L) = log₁₀(Λ) + ((d+1)/2) · log₁₀(p)
```

斜率由公式固定为 (d+1)/2，拟合截距给出**压制因子 Λ**。Λ 越小，压制效果越好。

### 运行
```bash
python -m surface_code_study.experiments.exp2_pl_vs_d
```

### 输出
- `results/exp2_pl_vs_d.json` — 原始数据 + Λ 拟合结果
- `results/exp2_pl_vs_d.png` — semilogy 绘图
- `results/exp2_pl_vs_d.pdf` — 矢量图

### 调用流程
与实验1完全一致，仅参数不同：
```python
# 固定 p=0.1%，扫描 d
circuit = build_surface_code_circuit(
    d=d,                  # 变化的参数
    platform_params=platform_params,
    rounds=d,
    p=P_FIXED,           # 固定为 0.001
)

result = run_adaptive_experiment(
    circuit=circuit,
    num_rounds=d,
    d=d,
    platform_name=platform_name,
    p_scale=P_FIXED,
    min_logical_errors=100,
)
```

### Λ 拟合
实验2额外对每个平台拟合压制因子 Λ：
```python
# x = (d+1)/2, y = log10(PL)
# 斜率固定为 log10(p_fixed)，只拟合截距 log10(Λ)
log_lambda = np.sum(weights * (y - slope_fixed * x)) / np.sum(weights)
lambda_val = 10 ** log_lambda
```

---

## 实验3：综合对比

**脚本**: `exp3_platform_compare.py`

### 研究问题
综合对比三个平台的性能，包含实验1和实验2的所有图表，并额外计算：
- 达到 PL=10⁻⁶ 所需的最小码距
- 生成汇总表

### 运行
```bash
python -m surface_code_study.experiments.exp3_platform_compare
```

### 输出
- `results/exp3_platform_compare.json` — 完整数据和汇总表
- `results/exp3_platform_compare.png` — 综合对比图
- `results/exp3_platform_compare.pdf` — 矢量图

---

## 共同框架

三个实验共享相同的调用模式：

```python
# 1. 获取平台参数
from surface_code_study.platforms import PLATFORMS

# 2. 构建电路
from surface_code_study.circuit_builder import build_surface_code_circuit
circuit = build_surface_code_circuit(d=d, platform_params=params, **kwargs)

# 3. 运行自适应采样
from surface_code_study.simulator import run_adaptive_experiment
result = run_adaptive_experiment(
    circuit=circuit,
    num_rounds=R,
    d=d,
    platform_name=name,
    p_scale=scale,
    min_logical_errors=100,
)

# 4. result 包含所有统计结果
print(f"PL = {result.pl:.3e} ± {result.pl_std:.3e}")
```

---

## 自适应采样机制

`run_adaptive_experiment()` 会自动调整采样数量：
- **停止条件**：积累到 `min_logical_errors`（默认100）个逻辑错误
- **上限**：最多 `max_shots`（默认10,000,000）次采样
- **统计精度**：100个错误 → 约10%相对误差

如果达到上限仍未满足目标，标记为 `[upper bound]`，表示 PL 极低（是真实值的上界）。

---

## 输出文件格式

### JSON 结构
```json
{
  "platform_name": [
    {
      "platform": "superconducting",
      "d": 5,
      "rounds": 5,
      "p_scale": 0.5,
      "PL": 2.34e-5,
      "PL_std": 2.34e-6,
      "P_run": 0.000234,
      "shots": 427000,
      "logical_errors": 100,
      "hit_max_shots": false,
      "time_seconds": 12.5
    }
  ]
}
```

### SimulationResult 关键字段

| 字段 | 含义 |
|------|------|
| `pl` | 逻辑错误率 per cycle |
| `pl_std` | PL 的标准误差 |
| `p_run` | 单次实验的整体错误概率 |
| `num_shots` | 总采样数 |
| `num_logical_errors` | 积累的逻辑错误数 |
| `hit_max_shots` | 是否达到采样上限 |
| `time_seconds` | 运行耗时（秒） |
