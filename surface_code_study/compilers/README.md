# 平台感知编译器

针对不同量子平台编译表面码电路的编译器。每个编译器将抽象的 rotated surface code 布局映射为具有物理意义的 stim 电路，包含平台特定的门调度、qubit 输运和 idle 退相干。

## 架构

```
PlatformParams (platforms.py)
    │  各平台的噪声参数：门/测量/复位错误率、
    │  T1/T2 相干时间、相对误差比例。
    │
    └── compilers/__init__.py (get_compiler → 工厂函数)
            │  将基础噪声参数与平台特有线参数合并
            │  （输运时间、区域相干性等）。
            │
            ├── base.py          PlatformCompiler 抽象基类
            │   ├── _build_rotated_layout()   共享的 d²×d² 网格布局
            │   ├── build_memory_circuit()    构建 stim memory experiment
            │   ├── idle_noise()              T1/T2 → Pauli 信道
            │   └── idle_noise_except()       反向 qubit 选取
            │
            ├── superconducting.py  4 步定向 CZ 调度 (N/W/S/E)
            ├── neutral_atom.py     双区移动 + Rydberg 门
            └── trapped_ion.py      逐对离子输运 + MS 门
```

## 各组件所做假设

### 基类 (`base.py`)

1. **统一 qubit 空间** — 所有 qubit 共享相同的 T1/T2，除非通过 `idle_noise()` 的 `T1_us`/`T2_us` 参数显式覆写。框架没有内建的"区域"概念来区分不同的相干属性。

2. **idle 噪声 = 不对称 Pauli 信道** — idle 退相干建模为 `PAULI_CHANNEL_1(px, py, pz)`，其中 `px = py = 0.25·(1 − exp(−t/T1))`，`pz = 0.5·(1 − exp(−t/T2)) − px`。这是标准的零温 qubit 退相干模型，假设振幅阻尼（T1）和纯退相（T2）是仅有的 idle 误差来源。

3. **强制执行 T2 ≤ 2·T1** — `T2` 被钳制到 `2·T1`，因为纯退相率 `1/Tφ = 1/T2 − 1/(2·T1)` 必须非负。

4. **仅支持 rotated surface code** — 只有 `_build_rotated_layout()` 一种布局。它生成标准的 d² 个数据 qubit + d²−1 个辅助 qubit 的棋盘格，排列在 2d×2d 网格上。不支持其他纠错码（unrotated、colour code、qLDPC 等）。

5. **逻辑 Z 可观测量 = 最左列** — `_add_logical_observable()` 硬编码最小列坐标数据 qubit 的乘积作为逻辑 Z 算子。逻辑 X 未定义，边界类型（rough vs. smooth）隐含在布局构建器中而非显式体现在可观测量里。

6. **仅支持 memory experiment** — `build_memory_circuit()` 构建固定结构：数据 qubit |0⟩ 初始化 → N 轮稳定子提取 → 数据测量 → OBSERVABLE_INCLUDE。不支持态制备或逻辑门实验。

7. **所有辅助 qubit 物理等价** — 所有辅助 qubit 共用相同的复位、单 qubit 门和测量错误率。不区分 flag qubit、ghost ancilla、leakage 检测等角色。

8. **stim qubit 索引是连续的** — 数据 qubit 占据索引 0 .. d²−1，辅助 qubit 占据 d² .. 2d²−2。所有布局遍历都依赖此顺序。

9. **DETECTOR 语义** — 第一轮 detector 仅引用 Z 辅助 qubit 的测量结果（从 |0⟩ 初始化的确定性结果）。后续轮次比较连续两次辅助 qubit 测量。不支持实验中途复位或 leakage。

10. **所有 qubit 始终存在于电路中** — stim 电路在整个实验期间包含所有 qubit。idle 噪声是对"不操作"的建模手段，qubit 从不会被临时移除。

### 超导平台 (`superconducting.py`)

11. **4 步定向 CZ 调度 (N→W→S→E)** — 假设 CZ 门可以划分为四个互不重叠的方向层。不做频率碰撞检查；真实 transmon 可能需要更复杂的调度策略。

12. **门 tick = 5% 周期，测量 = 80%** — 周期时间分配为 4 × 5%（四个 CZ tick）加 80%（测量 tick）。这些比例是对典型 transmon 处理器的粗略估计，未对特定器件标定。

13. **所有 qubit 共享同一芯片** — T1/T2 在数据和辅助 qubit 间均匀一致。不模拟频率无序、两级系统缺陷和结老化。

14. **忽略读出串扰** — 假定邻近数据 qubit 不受辅助 qubit 读出脉冲影响，超出测量 tick 所捕捉的 idle 退相干。

15. **无 leakage 模型** — 不模拟 transmon 向 |2⟩ 态的泄漏；所有误差由 |0⟩/|1⟩ 能级内的 depolarising 和 Pauli 信道捕捉。

### 中性原子平台 (`neutral_atom.py`)

16. **双区架构** — 编译器假设存在存储区（基态超精细 qubit，T1 ~ 1 s，T2 ~ 1 ms）和纠缠区（Rydberg 态，T1_r ~ 100 μs，T2_r ~ 100 μs）。存储区是隐式的：当前未被移动或门控的 qubit 默认处于存储区。

17. **移动期间使用存储区 T1/T2** — 光镊输运中的原子仍处于基态，因此移动阶段使用存储区 T1/T2。不模拟输运过程中的运动激发和差分光移。

18. **移动期间所有 qubit 都经历 idle 时间** — 在每个移动 batch 中，**所有** qubit（被移动和未被移动的）都以存储区 T1/T2 经历 idle 退相干。被移动的原子在基态输运；未被移动的原子在存储区等待。

19. **门脉冲期间的 Rydberg 态 idle** — 激发到 Rydberg 态做 CZ 门的原子，在门脉冲期间（~0.1 μs）以 Rydberg T1/T2 经历额外的 idle 退相干。这与 `DEPOLARIZE2` 门误差是分开的，后者捕捉激光和控制的不完美。

20. **每个 batch 使用全局 CZ** — 同一方向 batch 内的所有 (辅助, 数据) 对通过单次全局 Rydberg 脉冲同时纠缠。假设 Rydberg blockade 半径足够大以防止对间串扰；不模拟向非目标原子的 blockade 泄漏。

21. **纠缠区容量无上限** — `_schedule_movement_batches()` 不限制每个 batch 的原子对数量。实际纠缠区具有有限空间和有限光学接入。

22. **base T1/T2 即为存储区值** — 对于该平台，基础 `T1_us` 和 `T2_us` 参数被解释为存储区值，因为基态占据了 qubit 绝大部分的时间。仅将 `T1_rydberg_us` 和 `T2_rydberg_us` 作为平台额外参数。

23. **所有方向的移动时间相同** — `t_move_ns` 对所有四个方向 batch 统一。实际输运时间可能因原子排列方式而随方向变化。

### 离子阱平台 (`trapped_ion.py`)

24. **双区 QCCD 模型** — 编译器将 QCCD 架构简化为两个区：A 区放辅助 qubit，B 区放数据 qubit。实际 QCCD 处理器拥有数十个可独立寻址的 trap zone。

25. **逐对输运** — 每次 (辅助, 数据) 交互需要两次完整输运：辅助 qubit 移到数据区 → 门操作 → 辅助 qubit 移回。不模拟流水线优化（一次行程访问多个数据 qubit）。

26. **MS gate ≈ CZ + 单 qubit 旋转** — Mølmer-Sørensen 门用夹在 Hadamard 之间的 CZ 门近似，二者 Clifford 等价。MS 门特有的非 Clifford 误差信道（如运动模式激发）未被捕捉。

27. **声子加热可选且当前为零** — `p_heating = 0.0` 禁用了离子输运期间的声子加热信道。实际阱中反常加热是显著的噪声源。

28. **所有输运时长相同** — `t_transport_ns` 对任意两个 qubit 的交互统一。实际输运时间取决于 trap zone 之间的物理距离。

29. **测量错误主导读出** — `p_meas = 0.6%` 模拟了多区 trap 中的读出串扰，但不区分布居数荧光误差和探测效率不足。

### 跨平台共同假设

30. **无 leakage 和 erasure 误差** — 三个编译器均在 Pauli 误差层面工作（depolarising + Pauli 信道）。不模拟向非计算能级的泄漏（transmon 的 |2⟩ 态、Rydberg 反俘获、离子运动激发）和 erasure 转换。

31. **跨轮次误差无关联** — 独立轮次的误差互不相关。不捕捉低频电荷噪声（1/f）、温度漂移和激光相位漂移等现象。

32. **门时长是数量级估计** — `t_cycle_ns`、`t_move_ns` 和 `t_transport_ns` 是文献中代表性数值，未针对具体器件标定。

## idle 噪声模型

`idle_noise()` 方法接受可选的 `T1_us` 和 `T2_us` 覆写参数：

```python
def idle_noise(self, qubits, duration_ns, T1_us=None, T2_us=None):
    """
    由 T1/T2 生成不对称 Pauli 信道。

    覆写参数允许平台编译器在不修改 self.params 的情况下
    指定区域相关的相干时间：
      - T1_us, T2_us = None   → 使用 self.params 中的默认值
      - T1_us, T2_us = float  → 使用传入的值
    """
```

这使得中性原子编译器可以在门控阶段传入 Rydberg 态的 T1/T2，同时在移动和测量阶段使用基础（存储区）T1/T2。

## 零噪声测试

当基础参数传入 `T1_us > 1e9`（等效于无穷大）时，工厂函数自动将其传播到所有区域相关的 `T1_*` 和 `T2_*` 变体。这使得零噪声测试只需设置基础 T1/T2 即可。
