# 中性原子量子计算平台物理实现综述与参数整理

## 第一部分 物理实现综述

中性原子量子计算平台的基本思路，是把原子内部的长寿命能级作为量子比特，并利用光学手段完成俘获、排布、操控和测量。与超导平台不同，这一体系的物理对象本身就是近乎理想的原子，因此其优点首先体现在相干时间长、阵列可重构以及几何布局高度灵活，而其代价则集中表现在双比特门需要借助高激发态相互作用，且稳定子提取往往伴随显著的移动和等待时间<sup>[1][2][3]</sup>。在当前主流路线中，量子比特通常编码在中性原子基态超精细能级上，而双比特纠缠则通过短暂激发到 Rydberg 态实现。若记两能级计算子空间为 $|0\rangle$ 与 $|1\rangle$，Rydberg 态记为 $|r\rangle$，则单原子的驱动哈密顿量可以写成

$$
H_{1} = \frac{\Omega(t)}{2} \left( |1\rangle \langle r| + |r\rangle \langle 1| \right) - \Delta |r\rangle \langle r|,
$$

其中 $\Omega(t)$ 表示时间相关的驱动强度，$\Delta$ 表示失谐量。该式说明，外部光场可以把基态和 Rydberg 态之间建立受控耦合，而失谐量决定有效动力学是偏向真实布居转移，还是偏向虚激发产生的相位累积<sup>[2][4]</sup>。对于两个原子，当两者同时占据 Rydberg 态时，会产生强烈的相互作用能移。若以 $V(R)$ 表示两原子间距离 $R$ 上的相互作用，则常见近似为 van der Waals 形式

$$
V(R) = \frac{C_6}{R^6},
$$

其中 $C_6$ 是与所选 Rydberg 态相关的系数。于是两原子体系的有效哈密顿量可以写成

$$
H_{2} = \sum_{i=1}^{2} \left[ \frac{\Omega_i(t)}{2} \left( |1\rangle_i \langle r| + |r\rangle_i \langle 1| \right) - \Delta_i |r\rangle_i \langle r| \right] + V(R) \, |rr\rangle \langle rr| .
$$

当 $V(R)$ 足够大时，双激发态 $|rr\rangle$ 会被显著推出共振条件，这就是 Rydberg blockade 的物理基础。其结果是，两原子系统的动力学不再是两个彼此独立的单原子驱动，而会出现条件相位积累或条件激发抑制，从而实现受控相位门或与之等价的双比特门<sup>[2][4][5]</sup>。因此，中性原子平台的双比特门能力并不来自固定金属线路中的电路耦合，而来自可由原子间距离和激发态选择共同调控的相互作用。

中性原子平台之所以适合 surface code，并不在于它天然拥有二维最近邻网格，而在于它能够通过光学镊子把原子阵列重排成适合稳定子提取的几何结构。对于 surface code，需要把数据比特和辅助比特组织成规则平面阵列，并反复测量局域稳定子。中性原子阵列的一个突出优点是，原子的位置可以在实验过程中重新排布，因此系统并不被永久固定在单一拓扑上<sup>[1][2]</sup>。然而，这个优点在进入真实纠错时又会反过来成为成本来源。原因是原子移动并非瞬时过程，任何把原子从存储区运送到纠缠区的操作，都会在门操作之外增加额外等待时间，从而引入新的退相干预算。于是，对中性原子平台而言，逻辑错误率不仅由门保真度决定，也由阵列重排和移动调度的时间代价决定。

单比特门通常通过微波或双光子 Raman 过程作用在基态超精细能级之间完成。若记单比特门持续时间为 $T_{1Q}$，基态存储区的能量弛豫时间为 $T_{1,s}$，相干时间为 $T_{2,s}$，则单比特门误差可近似写成

$$
e_{1Q} \approx 1 - \exp\!\left(- a_1 \frac{T_{1Q}}{T_{1,s}} - b_1 \frac{T_{1Q}}{T_{2,s}} \right) + e_{\mathrm{ctrl},1Q},
$$

其中 $a_1$ 与 $b_1$ 是与脉冲方案相关的无量纲系数，$e_{\mathrm{ctrl},1Q}$ 表示激光幅度噪声、相位噪声和失谐误差等控制误差贡献。由于基态超精细能级的寿命极长，单比特门误差通常不由能量弛豫主导，而更多由控制精度和退相位限制<sup>[2][3]</sup>。这也是为什么中性原子平台在当前文献中往往能够给出优于 $10^{-3}$ 量级的单比特门保真度。

双比特门的情况不同。双比特门必须把参与相互作用的原子激发到 Rydberg 态，而 Rydberg 态虽然提供了强相互作用，也显著缩短了有效相干时间。若记双比特门持续时间为 $T_{2Q}$，Rydberg 态寿命为 $T_{1,r}$，Rydberg 态相干时间为 $T_{2,r}$，则双比特门误差可以写成

$$
e_{2Q} \approx 1 - \exp\!\left(- a_2 \frac{T_{2Q}}{T_{1,r}} - b_2 \frac{T_{2Q}}{T_{2,r}} \right) + e_{\mathrm{ctrl},2Q},
$$

其中 $e_{\mathrm{ctrl},2Q}$ 表示激发脉冲不完美、相位积累误差和原子间距离波动带来的误差项。与超导平台相比，中性原子平台的双比特门误差更容易受到几何排布和态寿命的共同影响，因为相互作用强度本身就是距离相关量，而门过程又必须经过高激发态<sup>[2][4][5]</sup>。这就是为什么中性原子平台的代表性双比特门错误率通常高于超导和离子阱中的最佳单比特门结果，同时也解释了为什么当前 benchmark 中把双比特门通道视为平台区分度最高的基本量之一。

测量通常通过状态选择性的荧光读出完成。其基本思路是利用一个对某一内部态共振的探测光场，使被测原子在该态上产生强散射，而另一个态保持近似暗态，从而把内部量子态转化为可由成像系统记录的荧光信号<sup>[2][6]</sup>。对 surface code 而言，测量带来的首要问题不是读出原理，而是时间和重复性。辅助比特测量时，尚未参与当前读出的数据比特仍然必须保持相干；若还需要在测量之后执行阵列重排或重新装载，则测量与复位过程会进一步拉长单轮稳定子提取周期。若记测量时长为 $T_{\mathrm{meas}}$，重置或重新准备时长为 $T_{\mathrm{reset}}$，则单轮稳定子周期可写为

$$
T_{\mathrm{cycle}} = m T_{1Q} + n T_{2Q} + N_{\mathrm{move}} T_{\mathrm{move}} + T_{\mathrm{meas}} + T_{\mathrm{reset}},
$$

其中 $m$ 和 $n$ 分别表示单轮内的单比特门层数和双比特门层数，$T_{\mathrm{move}}$ 表示一次原子移动的时间，$N_{\mathrm{move}}$ 表示单轮内移动批次数。这个公式比超导平台多出的项，就是移动项 $N_{\mathrm{move}} T_{\mathrm{move}}$。在中性原子平台上，这一项经常不是修正，而是主导项，因为门脉冲持续时间通常远短于光学镊子重排或运送的时间<sup>[1][2][3]</sup>。

如果只考察存储区中的等待过程，令等待时长为 $t_{\mathrm{idle},s}$，则相应的 idle 误差概率可以近似表示为

$$
p_{\mathrm{idle},s} \approx 1 - e^{- t_{\mathrm{idle},s} / T_{2,s}} .
$$

这里选用 $T_{2,s}$ 而非 $T_{1,s}$ 作为主导尺度，是因为在中性原子基态存储区中，能量弛豫时间通常远长于实验周期，退相位往往更先成为限制因素。若原子被激发到 Rydberg 态并在门脉冲期间停留时长 $t_{\mathrm{idle},r}$，则对应误差可写成

$$
p_{\mathrm{idle},r} \approx 1 - \exp\!\left(- \frac{t_{\mathrm{idle},r}}{T_{1,r}} - \frac{t_{\mathrm{idle},r}}{T_{2,r}} \right) .
$$

这两个式子共同说明了中性原子平台的一个核心物理事实：当原子处于基态存储区时，系统可以获得很长的相干保持能力；但当系统为了双比特纠缠而进入 Rydberg 操作窗口时，误差预算会迅速恶化。因此，任何现实可行的纠错方案都必须尽量缩短原子进入纠缠区的时间，并降低移动过程对全局等待时间的累积。

当前项目中的 neutral atom compiler 正是以这一物理图景为基础。它把体系分成存储区和纠缠区两部分，并把每轮稳定子提取分解为若干批移动。每一批包含三段过程：首先把待操作的辅助比特和数据比特从存储区运送到纠缠区，其次执行 Rydberg 门，最后再把原子运回存储区。若单批移动时间记为 $t_{\mathrm{move}}$，单批门脉冲时间记为 $t_{\mathrm{gate}}$，总批次数记为 $B$，则单轮内由移动和纠缠操作引起的主要时长为

$$
T_{\mathrm{NA,round}} \approx 2 B \, t_{\mathrm{move}} + B \, t_{\mathrm{gate}} + T_{\mathrm{meas}}.
$$

在当前代码设定下，$B=4$，$t_{\mathrm{move}} = 200\,\mu\mathrm{s}$，$t_{\mathrm{gate}} = 0.1\,\mu\mathrm{s}$。因此，仅移动部分就带来大约 $1.6\,\mathrm{ms}$ 的时间开销，而门脉冲本身几乎可以忽略。这一数量级比较直接揭示了为什么中性原子平台在本项目中会出现由 idle 主导而非由门误差主导的逻辑错误率结构。不是因为门本身不够好，而是因为完成一次局域稳定子测量所需的全系统等待时间太长。

若把各类物理误差合并为单轮等效物理错误率 $p_{\mathrm{eff}}$，则可以写成

$$
p_{\mathrm{eff}} = c_1 e_{1Q} + c_2 e_{2Q} + c_3 e_{\mathrm{meas}} + c_4 e_{\mathrm{reset}} + c_5 p_{\mathrm{idle},s} + c_6 p_{\mathrm{idle},r},
$$

其中 $e_{\mathrm{meas}}$ 表示测量错误率，$e_{\mathrm{reset}}$ 表示重置错误率，$c_1,\dots,c_6$ 是由稳定子提取电路结构和调度方式决定的灵敏度系数。若平台进入容错门槛以下区间，则逻辑错误率 $P_L$ 与码距 $d$ 的关系可用

$$
P_L \approx A \left( \frac{p_{\mathrm{eff}}}{p_{\mathrm{th}}} \right)^{\frac{d+1}{2}}
$$

近似描述，其中 $A$ 是与具体实现相关的常数，$p_{\mathrm{th}}$ 表示门槛错误率。对中性原子平台而言，这个式子最重要的含义不是单纯说明码距增大有助于纠错，而是提醒我们：若 $p_{\mathrm{eff}}$ 被移动引起的等待误差抬高到足够大，则增加码距未必会换来逻辑改进，因为更大的码距又会带来更多原子、更多调度批次和更长的全局等待时间。

因此，中性原子平台的物理实现可以概括为如下命题。它利用基态原子的长相干时间和可重构阵列提供了很强的几何可塑性，这使它在理论上极适合大规模二维纠错结构；但一旦进入真实的 surface code 稳定子提取流程，门操作不再是唯一成本，移动、等待和纠缠区短寿命态共同构成了逻辑错误率的主要来源。也正因为如此，在这一平台上，任何只根据门保真度做出的 benchmark 结论都会偏乐观，而把移动与区域相干时间显式纳入模型之后，逻辑错误率的主导项就会发生显著变化。

## 第二部分 官方数据整理与参数映射

若要把中性原子平台的公开结果导入当前 benchmark，需要先区分哪些量可以直接从文献读取，哪些量只是为了仿真必须引入的工程参数。前者包括单比特门错误率、双比特门错误率、测量错误率、基态存储区的相干时间以及 Rydberg 门相关时间尺度；后者包括 reset 误差、每轮的聚合 idle 概率以及编译器所需的移动批次数和总周期时间。当前项目的 `surface_code_study/platforms.py` 与 `surface_code_study/compilers/__init__.py` 正是按这种方式拆分参数的。进一步核对企业级公开资料后可以看到，QuEra 官方页面能够直接支持“中性原子具备超过 $1\,\mathrm{s}$ 的长相干时间”和“平台支持 coherent shuttling 与 zoned architecture”这类架构级信息，但并没有公开一张稳定的单比特门、双比特门和 SPAM 指标表。因此，本节数值仍需以代表性论文和补充材料为主，企业页面更多承担架构与可扩展性佐证的角色<sup>[D3]</sup>。

在本项目中，中性原子的基础字段包括 `p_gate_1q`、`p_gate_2q`、`p_meas`、`p_reset`、`p_idle`、`cycle_time_us`、`T1_us` 和 `T2_us`。其中 `T1_us` 与 `T2_us` 被解释为存储区基态原子的时间尺度。进一步地，compiler 额外引入 `t_move_ns`、`t_gate_ns`、`t_cycle_ns`、`n_move_batches`、`T1_rydberg_us` 和 `T2_rydberg_us`，分别表示单次移动时间、Rydberg 门脉冲时间、单轮等效总时长、移动批次数和纠缠区的相干时间。根据当前仓库默认配置，这些量分别取为 $p_{1Q}=10^{-3}$、$p_{2Q}=6\times 10^{-3}$、$p_{\mathrm{meas}}=5\times 10^{-3}$、$p_{\mathrm{reset}}=5\times 10^{-3}$、$p_{\mathrm{idle}}=10^{-3}$、$T_{1,s}=1\,\mathrm{s}$、$T_{2,s}=1\,\mathrm{ms}$、$t_{\mathrm{move}}=200\,\mu\mathrm{s}$、$t_{\mathrm{gate}}=0.1\,\mu\mathrm{s}$、$T_{1,r}=100\,\mu\mathrm{s}$、$T_{2,r}=100\,\mu\mathrm{s}$<sup>[2][3]</sup>。

为了区分公开文献值和当前 benchmark 采用值，可把最关键的中性原子参数整理为表 1。表中“官方代表值”表示可从代表性论文中直接读出的数量级，“当前代码值”表示仓库默认设置，“建议解释”指出该量是否已经是文献直接量，还是当前 benchmark 的工程估计量。

| 参数 | 物理意义 | 官方代表值 | 当前代码值 | 建议解释 |
| --- | --- | --- | --- | --- |
| `p_gate_1q` | 单比特门错误率 | 约 $10^{-3}$ 量级<sup>[2][3]</sup> | $1.0 \times 10^{-3}$ | 与文献量级一致 |
| `p_gate_2q` | Rydberg 双比特门错误率 | 约 $6 \times 10^{-3}$ 量级<sup>[2][3]</sup> | $6.0 \times 10^{-3}$ | 与代表性结果一致 |
| `p_meas` | 测量错误率 | 约 $5 \times 10^{-3}$ 量级<sup>[2]</sup> | $5.0 \times 10^{-3}$ | 量级合理 |
| `T1_us` | 存储区能量弛豫时间 | 约 $1\,\mathrm{s}$ 量级<sup>[2][3]</sup> | $1.0 \times 10^{6}$ 微秒 | 与量级一致 |
| `T2_us` | 存储区相干时间 | 约 $1\,\mathrm{ms}$ 量级<sup>[2][3]</sup> | $1.0 \times 10^{3}$ 微秒 | 与量级一致 |
| `T1_rydberg_us` | Rydberg 态寿命 | 约 $100\,\mu\mathrm{s}$ 量级<sup>[2][4]</sup> | $100$ 微秒 | 量级合理 |
| `T2_rydberg_us` | Rydberg 态相干时间 | 约 $100\,\mu\mathrm{s}$ 量级<sup>[2][4]</sup> | $100$ 微秒 | 量级合理 |
| `t_move_ns` | 单次移动时间 | 百微秒量级<sup>[2][3]</sup> | $200000$ 纳秒 | 属于编译器建模量 |
| `t_gate_ns` | 门脉冲时间 | 亚微秒量级<sup>[2][4]</sup> | $100$ 纳秒 | 属于编译器建模量 |
| `p_reset` | 复位误差 | 文献常不直接按此字段给出 | $5.0 \times 10^{-3}$ | 当前 benchmark 工程估计 |
| `p_idle` | builtin 中每轮 idle 噪声 | 文献不直接给出 | $1.0 \times 10^{-3}$ | 当前 benchmark 工程估计 |

表 1 表明，中性原子平台与超导平台不同，它在当前项目中的基础门误差与相干时间设定，反而与代表性公开结果比较接近；真正不够严格的部分主要集中在 `p_reset`、`p_idle` 以及若干时序参数的整合方式上。进一步做企业来源核查后，这个判断反而更清楚：QuEra 官方页面可以补强存储寿命、原子移动和分区架构这些高层事实，却没有给出足以直接替换表中 `p_gate_1q`、`p_gate_2q`、`p_meas` 或 `t_move_ns` 的完整企业数据表。因此，这些数值目前仍应被视作“以代表性学术结果为主、以企业架构信息为辅”的口径，而不应误写成“全部来自企业官网”。尤其值得注意的是，当前 `platforms.py` 里给出的 `cycle_time_us = 1.0` 微秒只具有表征意义，而 compiler 中真正使用的 `t_move_ns = 200000` 和 `t_cycle_ns = 800000` 纳秒才决定具体 idle 累积。但若把代码逐句展开可见，单轮实际包含 $4$ 个批次，每个批次都有两次移动，因此仅移动部分就已经达到 $1.6$ 毫秒量级，这与 `t_cycle_ns = 800000` 纳秒并不一致。也就是说，当前中性原子模型与超导模型一样，存在“文档口径”和“编译器真实时序口径”不完全统一的问题。

在当前代码中，统一扫描双比特门错误率时，其余通道按固定比例缩放。若以 $p$ 表示双比特门错误率基准，则有

$$
p_{1Q} = r_{1Q} p, \qquad p_{\mathrm{meas}} = r_{\mathrm{meas}} p, \qquad p_{\mathrm{reset}} = r_{\mathrm{reset}} p, \qquad p_{\mathrm{idle}} = r_{\mathrm{idle}} p,
$$

其中 $r_{1Q}$、$r_{\mathrm{meas}}$、$r_{\mathrm{reset}}$ 和 $r_{\mathrm{idle}}$ 分别是相对于双比特门误差的比例系数。对于当前项目的中性原子默认口径，有 $r_{1Q}=0.17$、$r_{\mathrm{meas}}=0.83$、$r_{\mathrm{reset}}=0.83$、$r_{\mathrm{idle}}=0.17$。这意味着当实验脚本显式传入统一的 $p$ 时，实际是在保持平台内部误差结构不变的前提下，对总体噪声水平做缩放。这种做法便于比较三平台，但并不意味着真实实验中所有通道都会严格按同一比例联动变化。

对于 builtin 路径，项目把 `p_gate_2q`、`p_meas`、`p_reset` 和 `p_idle` 直接映射到 stim 的聚合噪声接口，因此它更像一个忽略具体移动细节的等效模型。对于 compiler 路径，项目则显式区分存储区和纠缠区，利用 $T_{1,s}$、$T_{2,s}$、$T_{1,r}$、$T_{2,r}$ 以及移动和门脉冲时间，把同一轮稳定子提取拆成多段不同物理含义的等待过程。因此，compiler 模型能够表达一个对中性原子平台极其关键的事实，即逻辑错误率并不只是由门保真度决定，而是由门、移动、区域切换和全局等待时间共同决定。若后续要把官方数据更可信地导入本项目，中性原子平台至少需要完成三项校准。其一，应明确 `p_reset` 和 `p_idle` 的来源，避免把工程估计量误写为文献直接值。其二，应统一 `cycle_time_us`、`t_cycle_ns` 和根据移动批次实际展开得到的总时长三者之间的关系。其三，应在报告中明确指出，当前模型已经显式纳入移动与 Rydberg 区退相干，但尚未覆盖原子损失、再装载开销、成像串扰和空间不均匀性等更细粒度误差机制。

总的来说，中性原子平台在当前 benchmark 中最值得强调的并不是“门能否做得足够好”，而是“当真实移动和等待过程被写进模型后，长相干时间优势是否会被大规模稳定子提取的时序成本部分抵消”。这正是该平台在三类硬件路线比较中最有辨识度的物理问题，也是后续总报告中应重点展开的主线。

## 综述部分参考文献

[1] M. Saffman, T. G. Walker, and K. Mølmer, Quantum information with Rydberg atoms, Reviews of Modern Physics 82, 2313-2363, 2010.

[2] D. Bluvstein et al., Logical quantum processor based on reconfigurable atom arrays, Nature 627, 263-269, 2024.

[3] A. Omran et al., Generation and manipulation of Schrödinger cat states in Rydberg atom arrays, Science 365, 570-574, 2019.

[4] H. Levine et al., High-fidelity control and entanglement of Rydberg-atom qubits, Physical Review Letters 121, 123603, 2018.

[5] M. Saffman, Quantum computing with neutral atoms, National Science Review 6, 24-25, 2019.

[6] L. Henriet et al., Quantum computing with neutral atoms, Quantum 4, 327, 2020.

## 数据部分参考文献

[D1] D. Bluvstein et al., Logical quantum processor based on reconfigurable atom arrays, Nature 627, 263-269, 2024.

[D2] Supplementary information accompanying D. Bluvstein et al., Logical quantum processor based on reconfigurable atom arrays, Nature 627, 263-269, 2024.

[D3] QuEra Computing, Using Neutral-Atom Arrays to Build Quantum Computers, official platform page describing coherence times exceeding one second, coherent shuttling, and zoned neutral-atom architecture, https://www.quera.com/neutral-atom-platform, accessed 2026-06-11.