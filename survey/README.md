# 三平台统一参数表（基于当前代码）

本文档先冻结当前仓库中已经实现的 benchmark 参数口径，作为后续文献调研和参数回填的统一模板。这里的数值不是最终的"官方定版参数"，而是当前代码实际使用的默认输入，来源于以下两处：

- `surface_code_study/platforms.py`：平台基础噪声参数与 T1/T2。
- `surface_code_study/compilers/__init__.py`：平台感知编译器额外时序参数。

## 1. 统一字段定义

| 字段 | 单位 | 含义 | builtin 模型是否使用 | compiler 模型是否使用 | 当前代码入口 |
| --- | --- | --- | --- | --- | --- |
| `p_gate_1q` | 每次操作的概率 | 单比特门错误率 | 间接使用，主要通过统一缩放保留比例 | 直接使用 | `platforms.py` |
| `p_gate_2q` | 每次操作的概率 | 双比特门错误率，也是显式 `p` 扫描时的基准量 | 直接使用 | 直接使用 | `platforms.py` |
| `p_meas` | 每次测量的概率 | 测量错误率 | 直接使用 | 直接使用 | `platforms.py` |
| `p_reset` | 每次复位的概率 | 复位错误率 | 直接使用 | 直接使用 | `platforms.py` |
| `p_idle` | 每轮的概率 | builtin 中的数据比特 idle 退极化率 | 直接使用 | 不直接使用 | `platforms.py` |
| `cycle_time_us` | 微秒 | builtin 模型的表征性单轮时间 | 仅文档语义，不直接参与 stim 噪声计算 | 不使用 | `platforms.py` |
| `T1_us` | 微秒 | 能量弛豫时间 | 不使用 | 直接用于 idle 噪声信道 | `platforms.py` |
| `T2_us` | 微秒 | 相干时间 | 不使用 | 直接用于 idle 噪声信道 | `platforms.py` |
| `relative_scales` | 无量纲 | 显式 `p` 扫描时，各噪声相对 `p_gate_2q` 的比例 | 直接使用 | 直接使用 | `platforms.py` |
| `t_cycle_ns` | 纳秒 | compiler 中单轮 syndrome extraction 的等效时长 | 不使用 | 平台相关 | `compilers/__init__.py` |
| `t_move_ns` | 纳秒 | 中性原子每次移动耗时 | 不使用 | 仅中性原子使用 | `compilers/__init__.py` |
| `t_gate_ns` | 纳秒 | 中性原子 Rydberg 门脉冲时长 | 不使用 | 仅中性原子使用 | `compilers/__init__.py` |
| `n_move_batches` | 无量纲 | 中性原子每轮移动批次数 | 不使用 | 仅中性原子使用 | `compilers/__init__.py` |
| `T1_rydberg_us` | 微秒 | 中性原子 Rydberg 态寿命 | 不使用 | 仅中性原子使用 | `compilers/__init__.py` |
| `T2_rydberg_us` | 微秒 | 中性原子 Rydberg 态相干时间 | 不使用 | 仅中性原子使用 | `compilers/__init__.py` |
| `t_transport_ns` | 纳秒 | 离子阱输运时长 | 不使用 | 仅离子阱使用 | `compilers/__init__.py` |
| `p_heating` | 每次输运的概率 | 离子阱输运加热误差 | 不使用 | 仅离子阱使用 | `compilers/__init__.py` |

## 2. 当前代码默认值总表

### 2.1 基础平台参数

| 平台 | 代表系统 | `p_gate_1q` | `p_gate_2q` | `p_meas` | `p_reset` | `p_idle` | `cycle_time_us` | `T1_us` | `T2_us` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Superconducting | Google Willow | `3e-4` | `1e-3` | `5e-3` | `1e-4` | `1e-2` | `1.0` | `100` | `100` |
| Neutral Atom | Harvard / QuEra | `1e-3` | `6e-3` | `5e-3` | `5e-3` | `1e-3` | `1.0` | `1e6` | `1e3` |
| Ion Trap | Quantinuum H2 | `1e-4` | `1e-3` | `6e-3` | `1e-3` | `1e-6` | `10.0` | `1e7` | `1e7` |

### 2.2 `relative_scales` 统一比例

显式传入 `p` 时，代码会把 `p` 解释成 `p_gate_2q`，其余噪声通道按以下比例联动缩放。

| 平台 | `gate_1q` | `gate_2q` | `meas` | `reset` | `idle` |
| --- | --- | --- | --- | --- | --- |
| Superconducting | `0.3` | `1.0` | `5.0` | `0.1` | `10.0` |
| Neutral Atom | `0.17` | `1.0` | `0.83` | `0.83` | `0.17` |
| Ion Trap | `0.1` | `1.0` | `6.0` | `1.0` | `1e-3` |

### 2.3 compiler 额外时序参数

| 平台 | 额外参数 | 当前值 | 物理含义 |
| --- | --- | --- | --- |
| Superconducting | `t_cycle_ns` | `200` | 编译器中单轮的等效总时长，按 4 个 gate tick 加 1 个 measurement tick 划分 |
| Neutral Atom | `t_move_ns` | `200000` | 单次光镊移动耗时 |
| Neutral Atom | `t_gate_ns` | `100` | Rydberg 门脉冲时长 |
| Neutral Atom | `t_cycle_ns` | `800000` | 单轮总时长 |
| Neutral Atom | `n_move_batches` | `4` | 每轮 4 个方向批次 |
| Neutral Atom | `T1_rydberg_us` | `100` | Rydberg 态寿命 |
| Neutral Atom | `T2_rydberg_us` | `100` | Rydberg 态相干时间 |
| Ion Trap | `t_transport_ns` | `2000000` | 单次离子输运耗时 |
| Ion Trap | `t_cycle_ns` | `20000000` | 单轮总时长 |
| Ion Trap | `p_heating` | `0.0` | 当前未启用的输运加热项 |

## 3. 参数如何进入实验

### 3.1 builtin 路径

1. 实验脚本从 `PLATFORMS` 读取平台参数。
2. 若传入 `noise_scale`，则所有基础噪声按比例缩放。
3. 若显式传入 `p`，则令 `p_gate_2q = p`，再按 `relative_scales` 生成其余通道。
4. `build_surface_code_circuit()` 把参数映射到 stim 的 4 个聚合接口：
   - `after_clifford_depolarization`
   - `before_round_data_depolarization`
   - `before_measure_flip_probability`
   - `after_reset_flip_probability`

### 3.2 compiler 路径

1. 实验脚本先按 `noise_scale` 或显式 `p` 改写平台参数。
2. `get_compiler()` 把基础参数重命名为 `p_1q`、`p_2q`、`p_meas`、`p_reset`、`T1_us`、`T2_us`。
3. 工厂函数再合并平台特有时序参数，例如超导的 `t_cycle_ns`、中性原子的 `t_move_ns`、离子阱的 `t_transport_ns`。
4. 各平台编译器据此逐门构建电路，并在 idle 阶段通过 `T1/T2 -> Pauli channel` 建模退相干。

## 4. 目前这张表还存在哪些问题

这张表已经足够支持你开始做文献调研和报告搭架子，但还不能直接当成最终的"官方参考参数表"。至少还有四个待修正点：

1. 中性原子和离子阱中若干值在代码注释里仍标成 `estimate,待校准`。
2. `cycle_time_us` 与 compiler 里的 `t_cycle_ns` 并不总是严格一致，说明 builtin 与 compiler 现在是两套不同抽象层次。
3. 超导平台的默认 `p_gate_2q`、`p_meas`、`T1/T2` 比 Willow QEC 报告更理想化，后续要决定是保留"代表性参数"还是改成"官方中位数参数"。
4. builtin 模型不能完整表达平台特有时序和输运代价，所以最终报告要把 builtin 当作基线模型，把 compiler 当作物理实现模型。

## 5. 后续文献调研建议

后续给三平台补文献时，建议所有平台都沿着同一模板整理：

- 代表系统与年份
- 原生门集合
- 1Q / 2Q gate fidelity
- measurement / reset fidelity 与时长
- T1 / T2
- 连接性与额外调度代价
- 编译器需要的特有时序参数
- 当前代码值与官方值之间的偏差