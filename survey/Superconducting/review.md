# 超导量子计算平台物理实现综述与参数整理

## 第一部分 物理实现综述

超导量子计算平台的核心目标，是在宏观电路中构造出可被量子力学稳定描述的离散两能级系统，并使这些系统能够在芯片尺度上被批量制造、逐个寻址和相互耦合。当前主流路线以 transmon 为代表。它的出发点不是直接寻找天然存在的二能级微观粒子，而是在超导电路中引入约瑟夫森结，从而把原本接近线性谐振子的电磁模式改造为具有弱非线性的量子系统<sup>[1][2][3]</sup>。若用 $Q$ 表示结电容上的电荷，$C$ 表示总电容，$n$ 表示库珀对数目，$E_C$ 表示充电能，$E_J$ 表示约瑟夫森能，$\phi$ 表示超导相位差，则单个超导量子比特的有效哈密顿量可写为

$$
H = 4 E_C n^2 - E_J \cos \phi .
$$

这一表达式中的第一项给出电荷积累带来的能量代价，第二项给出库珀对穿过约瑟夫森结时的相位相关势能。若系统完全线性，则相邻能级之间的能量差保持常数，外部驱动无法只选择最低两级完成计算。约瑟夫森结提供的非线性使得最低两级跃迁频率 $\omega_{01}$ 与更高能级跃迁频率 $\omega_{12}$ 之间出现差值，这一差值通常记为非谐性 $\alpha = \omega_{12} - \omega_{01}$。transmon 通过令 $E_J / E_C \gg 1$ 抑制电荷噪声，使比特频率对背景电荷涨落不再高度敏感，同时保留足够的非谐性，使外部微波脉冲能够主要作用于 $|0\rangle$ 与 $|1\rangle$ 所张成的计算子空间<sup>[2][3]</sup>。

超导平台适合 surface code 的首要原因，是它天然支持二维局域耦合芯片。surface code 要求物理比特在平面上形成规则邻接结构，并重复执行最近邻稳定子测量。超导芯片通过固定的电容耦合或可调耦合器，把数据比特和辅助比特布置在近邻网格上，使每一次稳定子提取都能够被拆解为有限层数的最近邻双比特门与辅助比特测量序列<sup>[2][4]</sup>。这一点与离子阱和中性原子不同。后两者的长处在于可重构连通性或长相干时间，而超导平台的长处在于局域门操作速度快，单轮纠错周期可以压缩到微秒量级，从而在同一物理时间窗口内执行更多轮稳定子测量<sup>[5][6]</sup>。

单比特控制一般通过微波脉冲完成。若以 $\Omega(t)$ 表示时间相关的脉冲包络，$\omega_d$ 表示驱动频率，$\varphi$ 表示驱动相位，则在旋转波近似下，计算子空间中的控制哈密顿量可以写成

$$
H_d = \frac{\Omega(t)}{2} \left( \cos \varphi \, X + \sin \varphi \, Y \right),
$$

其中 $X$ 与 $Y$ 是计算子空间中的 pauli operator。这个表达式表明，脉冲包络决定旋转角速度，驱动相位决定旋转轴方向。若脉冲持续时间过短，则其频谱变宽，更容易激发到 $|2\rangle$ 等非计算态；若持续时间过长，则系统在操作中暴露于能量弛豫和退相位过程的时间增加。设 $T_{1Q}$ 为单比特门持续时间，$T_1$ 为能量弛豫时间，$T_2$ 为相干时间，则单比特门误差可以用一个近似表达式表示为<sup>[2][7]</sup>

$$
e_{1Q} \approx 1 - \exp\!\left(- a_1 \frac{T_{1Q}}{T_1} - b_1 \frac{T_{1Q}}{T_2} \right) + e_{\mathrm{leak},1Q},
$$

其中 $a_1$ 与 $b_1$ 是与具体脉冲形状相关的无量纲系数，$e_{\mathrm{leak},1Q}$ 表示泄漏到计算子空间之外的误差贡献。这个公式虽然不是严格从第一性原理直接推出的闭式定律，但它清楚地表达了一个工程事实：单比特门误差由退相干和泄漏共同决定，缩短时间并不必然等于减小误差，因为更短的脉冲同时会加重频谱外溢<sup>[2][7]</sup>。

双比特控制在超导平台上通常通过 CZ 门或与之等价的受控相位型相互作用实现。对于 surface code，双比特门是决定容错门槛的主导因素，因为每一轮稳定子提取都需要大量重复执行辅助比特与数据比特之间的耦合操作。若记 $T_{2Q}$ 为双比特门时长，$e_{2Q}$ 为双比特门误差，则类似地可写成

$$
e_{2Q} \approx 1 - \exp\!\left(- a_2 \frac{T_{2Q}}{T_1} - b_2 \frac{T_{2Q}}{T_2} \right) + e_{\mathrm{leak},2Q},
$$

其中 $a_2$ 与 $b_2$ 仍是与控制细节相关的系数，$e_{\mathrm{leak},2Q}$ 表示双比特门引起的非计算态布居。对于超导平台，双比特门误差通常高于单比特门误差，这是因为双比特门需要更复杂的频率调谐与相位补偿过程，同时更容易引入寄生耦合和泄漏<sup>[2][5]</sup>。因此，surface code benchmark 中把双比特门错误率单独列出并作为统一比较口径，是有明确物理依据的。

读取过程是超导平台与 surface code 相遇时最关键的物理环节之一。超导量子比特通常采用色散读取。设读出谐振腔的本征频率为 $\omega_r$，量子比特的跃迁频率为 $\omega_q$，两者耦合强度为 $g$，失谐量记为 $\Delta = \omega_q - \omega_r$。在大失谐条件下，有效哈密顿量可以写成<sup>[2][8]</sup>

$$
H_{\mathrm{disp}} \approx \left( \omega_r + \chi Z \right) a^\dagger a + \frac{1}{2} \left( \omega_q + \chi \right) Z,
$$

其中 $a^\dagger$ 与 $a$ 分别是谐振腔模式的产生与湮灭算符，$Z$ 是计算子空间中的 pauli operator，$\chi$ 表示色散频移。这个结果意味着，不同量子态会让谐振腔响应出现不同偏移，因此可以通过测量微波信号的相位或振幅变化来区分量子态。对 surface code 来说，问题不在于能否测量，而在于测量需要持续一个不可忽略的时间窗口。在该时间窗口中，许多数据比特并不执行门操作，只能保持等待，从而累积 idle 噪声<sup>[2][5][8]</sup>。

若令 $t_{\mathrm{idle}}$ 表示等待时长，则只考虑能量弛豫时，idle 引起的错误概率可以近似写为

$$
p_{\mathrm{idle}} \approx 1 - e^{- t_{\mathrm{idle}} / T_1} .
$$

若进一步把退相位也纳入，则更合适的做法是由 $T_1$ 和 $T_2$ 推出非对称 pauli channel。当前项目中的 compiler 正是采取这一思路：对未参与某一时间片门操作的比特施加基于 $T_1$ 和 $T_2$ 的 idle 噪声，而对测量阶段的数据比特给予最长的等待时长。于是，超导平台在 surface code 中的瓶颈不再只是门保真度本身，而是门调度、读出时长和等待时间三者共同决定的总误差预算。

如果把单轮稳定子提取周期记为 $T_{\mathrm{cycle}}$，把单轮内串行单比特门层数记为 $m$，双比特门层数记为 $n$，单比特门时长记为 $T_{1Q}$，双比特门时长记为 $T_{2Q}$，测量时长记为 $T_{\mathrm{meas}}$，复位时长记为 $T_{\mathrm{reset}}$，则有

$$
T_{\mathrm{cycle}} = m T_{1Q} + n T_{2Q} + T_{\mathrm{meas}} + T_{\mathrm{reset}} .
$$

这个公式说明了为什么超导平台虽然门速度快，但仍然可能受 idle 噪声主导。原因不是单次门操作太慢，而是每一轮稳定子提取中，读出与等待部分往往占据总周期的主要比例<sup>[5][6]</sup>。对于当前项目所采用的四步定向调度，单轮会被拆成四个双比特门时间片和一个测量时间片，这一结构与超导二维局域耦合的物理事实一致，也解释了为什么项目代码中特别强调测量时间片对逻辑错误率的贡献。

在容错分析中，最终关心的是逻辑错误率而不是单个物理过程的误差。若把各类物理误差综合为等效物理错误率 $p_{\mathrm{eff}}$，则可以写成

$$
p_{\mathrm{eff}} = c_1 e_{1Q} + c_2 e_{2Q} + c_3 e_{\mathrm{meas}} + c_4 e_{\mathrm{reset}} + c_5 p_{\mathrm{idle}},
$$

其中 $e_{\mathrm{meas}}$ 表示测量错误率，$e_{\mathrm{reset}}$ 表示复位错误率，$c_1,c_2,c_3,c_4,c_5$ 是由具体稳定子提取电路结构决定的灵敏度系数。若物理平台工作在门槛以下，则逻辑错误率 $P_L$ 会随码距 $d$ 的增加而下降，常用的近似写法为<sup>[4][9]</sup>

$$
P_L \approx A \left( \frac{p_{\mathrm{eff}}}{p_{\mathrm{th}}} \right)^{\frac{d+1}{2}},
$$

其中 $A$ 是与具体实现相关的常数，$p_{\mathrm{th}}$ 表示容错门槛。这个式子给出了一条非常直接的判断标准：若超导平台要在 surface code 上获得真正的逻辑改进，就必须同时压低双比特门误差、测量误差和 idle 误差，而不能只优化其中一项。Google Willow 的重要意义，就在于其公开结果已经展示出在重复纠错实验中进入 $P_L$ 随码距上升而下降的区间<sup>[5][6]</sup>。

总的来看，超导平台在三类硬件路线中的物理特征可以概括为如下命题。它依靠可制造的二维电路阵列获得了与 surface code 最匹配的几何结构，依靠微波控制获得了极快的门速度，但也因为相干时间仅在几十到上百微秒量级，而必须高度重视测量与等待过程中的空转噪声。正因为如此，任何针对超导平台的 benchmark，如果只保留聚合门错误模型而忽略读出与等待时长，就会倾向于给出偏乐观的逻辑错误率估计；如果进一步把时序、门深度和 idle 过程显式写入模型，结果才更接近真实器件运行的物理负担。

## 第二部分 官方数据整理与参数映射

为了把文献中的超导平台数据直接映射到本项目的 benchmark 初始化字段，需要先区分两种参数。第一种是文献直接给出的器件指标，如单比特门错误率、双比特门错误率、读出错误率、$T_1$ 和 $T_2$。第二种是为了完成仿真而必须补齐的建模参数，如每轮纠错周期、复位误差以及按代码接口拆分的 idle 噪声。前者目前主要来自 Google Quantum AI 的 Nature 主文与补充材料，而公开可直接访问的企业级页面则主要补充了 Willow 的平均 $T_1$ 和测量时间量级；后者仍需要在物理意义不变的前提下，按项目的数据结构做一致化映射<sup>[5][6]</sup>。

当前项目对超导平台使用的基础字段包括 `p_gate_1q`、`p_gate_2q`、`p_meas`、`p_reset`、`p_idle`、`cycle_time_us`、`T1_us` 和 `T2_us`。其中 `p_gate_1q` 与 `p_gate_2q` 分别对应单比特门错误率和双比特门错误率，`p_meas` 对应测量错误率，`p_reset` 对应复位错误率，`p_idle` 对应 builtin 模型中每轮数据比特的等待错误率，`cycle_time_us` 对应表征性的单轮周期时间，`T1_us` 与 `T2_us` 则供 compiler 路径生成 idle 噪声信道使用。进一步地，compiler 还需要 `t_cycle_ns` 这一时序参数，用于把一轮稳定子提取拆成多个门时间片和一个测量时间片。

根据 Google Quantum AI 公开的 Willow QEC 结果，可以把对本项目最关键的超导参考量整理为表 1。表中“官方代表值”指公开论文与官方规格表中可以直接对应到 benchmark 的量级；“当前代码值”指仓库默认输入；“建议解释”则指出该参数在使用时应被视作直接观测量还是建模量。

| 参数 | 物理意义 | 官方代表值 | 当前代码值 | 建议解释 |
| --- | --- | --- | --- | --- |
| `p_gate_1q` | 单比特门错误率 | 约 $3.5 \times 10^{-4}$<sup>[5][6]</sup> | $3.0 \times 10^{-4}$ | 可直接采用同量级值 |
| `p_gate_2q` | 双比特门错误率 | 约 $3.3 \times 10^{-3}$<sup>[5][6]</sup> | $1.0 \times 10^{-3}$ | 当前代码偏乐观，后续宜校准 |
| `p_meas` | 重复测量相关错误率 | 约 $7.7 \times 10^{-3}$<sup>[5][6]</sup> | $5.0 \times 10^{-3}$ | 当前代码偏乐观，且与 reset 拆分 |
| `T1_us` | 能量弛豫时间 | 约 $68$ 微秒量级<sup>[6]</sup> | $100$ 微秒 | 当前代码偏理想化 |
| `T2_us` | 相干时间 | 数十微秒量级<sup>[5][6]</sup> | $100$ 微秒 | 当前代码偏理想化 |
| `cycle_time_us` | 单轮稳定子提取时间 | 约 $1.1$ 微秒量级<sup>[5][6]</sup> | $1.0$ 微秒 | 量级接近 |
| `t_cycle_ns` | compiler 单轮等效时长 | 应与上项同量级 | $200$ 纳秒 | 当前代码明显偏快 |

进一步核对可见，表 1 中 `p_gate_1q`、`p_gate_2q` 和 `p_meas` 这三项仍主要由 Nature 主文和补充材料支撑，因为当前可公开访问的 Google 企业页面并未像 Quantinuum 那样给出一张稳定的逐指标数据表；企业页面当前能直接确认的是 Willow 平均 $T_1$ 已提升到 $68 \pm 13\,\mu\mathrm{s}$，以及超导测量过程约处在 $1\,\mu\mathrm{s}$ 量级<sup>[D3]</sup>。这意味着表中的门与测量错误率写法是“论文公开值”，而不是“企业官网独立再次列出的值”。在这种前提下，表 1 说明当前项目已经抓住了真正重要的参数种类，但具体数值仍带有代表性简化的痕迹。其中最明显的问题有两个。第一，双比特门误差和测量误差取值比 Willow QEC 公开结果更乐观，这会使逻辑错误率预测偏低。第二，compiler 中的 `t_cycle_ns = 200` 纳秒与 `cycle_time_us = 1.0` 微秒不一致，这意味着同一平台在 builtin 和 compiler 两条路径下对应了两套不同的时序尺度。若不修正这一点，就很难把两条路径的输出直接解释为同一器件在不同建模精度下的比较。

这些参数之间的关系也可以写成显式公式。若用 $p$ 表示统一扫描时采用的双比特门错误率基准，则在当前代码口径下，单比特门、测量和复位的基准值按固定比例缩放，即

$$
p_{1Q} = r_{1Q} p, \qquad p_{\mathrm{meas}} = r_{\mathrm{meas}} p, \qquad p_{\mathrm{reset}} = r_{\mathrm{reset}} p,
$$

其中 $r_{1Q}$、$r_{\mathrm{meas}}$ 和 $r_{\mathrm{reset}}$ 分别是相对于双比特门误差的比例系数。对于当前项目超导默认口径，有 $r_{1Q}=0.3$、$r_{\mathrm{meas}}=5.0$、$r_{\mathrm{reset}}=0.1$。这组比例不是新的物理定律，而是把平台内部噪声结构压缩成一组统一可调输入的工程做法。它的优点是便于跨平台扫描；它的不足是会掩盖同一平台内部各误差通道在不同实验条件下并不严格按固定比例变化这一事实。

对于 builtin 路径，项目直接把 `p_gate_2q` 映射到每轮 Clifford 之后的聚合退极化概率，把 `p_idle` 映射到每轮数据比特等待噪声，把 `p_meas` 和 `p_reset` 分别映射到测量前翻转和复位后翻转。这意味着 builtin 模型使用的是一种聚合噪声描述，它可以快速给出 surface code 的基线行为，却不会显式区分某一步等待是由读出引起还是由调度层数引起。对于 compiler 路径，项目则显式使用 $T_1$、$T_2$ 和时间片长度生成 idle channel，并在四步定向调度下对未参与门操作的比特分别施加等待噪声。这说明 compiler 模型能够表达“相同的门保真度，但不同的时间安排会产生不同逻辑错误率”这一物理事实，而这恰恰是超导平台与 surface code 结合时最不能忽视的问题。

因此，若后续要把官方数据真正导入本项目进行可信 benchmark，超导平台至少需要完成三项修正。第一，应把 `p_gate_2q`、`p_meas`、`T1_us` 和 `T2_us` 更新到与 Willow QEC 公开值同量级的区间，并在文档中说明所采用的是中位数、平均值还是代表值。第二，应统一 `cycle_time_us` 与 `t_cycle_ns` 的时序口径，使 builtin 与 compiler 至少在轮时长上对应同一类物理条件。第三，应在结果解读时明确指出，当前 compiler 虽然已经比 builtin 更接近真实硬件，但仍未显式纳入 leakage、读出串扰和频率碰撞等超导平台的重要误差机制。因此，它更适合作为“面向物理实现的近似 benchmark”，而不是对某一具体芯片的逐项复现实验。

## 综述部分参考文献

[1] J. Clarke and F. K. Wilhelm, Superconducting quantum bits, Nature 453, 1031-1042, 2008.

[2] P. Krantz, M. Kjaergaard, F. Yan, T. P. Orlando, S. Gustavsson, and W. D. Oliver, A quantum engineer's guide to superconducting qubits, Applied Physics Reviews 6, 021318, 2019.

[3] J. Koch, T. M. Yu, J. Gambetta, A. A. Houck, D. I. Schuster, J. Majer, A. Blais, M. H. Devoret, S. M. Girvin, and R. J. Schoelkopf, Charge-insensitive qubit design derived from the Cooper pair box, Physical Review A 76, 042319, 2007.

[4] A. G. Fowler, M. Mariantoni, J. M. Martinis, and A. N. Cleland, Surface codes: Towards practical large-scale quantum computation, Physical Review A 86, 032324, 2012.

[5] Google Quantum AI, Quantum error correction below the surface code threshold, Nature 638, 920-926, 2025.

[6] Supplementary information accompanying Google Quantum AI, Quantum error correction below the surface code threshold, Nature 638, 920-926, 2025.

[7] F. Motzoi, J. M. Gambetta, P. Rebentrost, and F. K. Wilhelm, Simple pulses for elimination of leakage in weakly nonlinear qubits, Physical Review Letters 103, 110501, 2009.

[8] A. Blais, R.-S. Huang, A. Wallraff, S. M. Girvin, and R. J. Schoelkopf, Cavity quantum electrodynamics for superconducting electrical circuits: An architecture for quantum computation, Physical Review A 69, 062320, 2004.

[9] E. Dennis, A. Kitaev, A. Landahl, and J. Preskill, Topological quantum memory, Journal of Mathematical Physics 43, 4452-4505, 2002.

## 数据部分参考文献

[D1] Google Quantum AI, Quantum error correction below the surface code threshold, Nature 638, 920-926, 2025.

[D2] Supplementary information accompanying Google Quantum AI, Quantum error correction below the surface code threshold, Nature 638, 920-926, 2025.

[D3] Google Research, Making quantum error correction work, official blog post introducing Willow and summarizing average $T_1$ and measurement-time scale, https://research.google/blog/making-quantum-error-correction-work/, accessed 2026-06-11.
