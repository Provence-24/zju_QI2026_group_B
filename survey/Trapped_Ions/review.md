# 离子阱量子计算平台物理实现综述与参数整理

## 第一部分 物理实现综述

离子阱量子计算平台的出发点，是把带电原子囚禁在电磁场形成的有效势阱中，并把离子内部两个稳定能级选作量子比特。与超导平台和中性原子平台不同，这一路线的基本载体既不是人工电路，也不是可自由重排的中性粒子阵列，而是受控束缚在真空装置中的离子链或分区离子寄存器。它的主要优势首先表现为内部态极稳定、相干时间极长以及门保真度高，而其主要代价则集中在多离子体系的输运、重排和读出时间上<sup>[1][2][3]</sup>。因此，离子阱平台在 surface code 中最关键的问题，通常不是单个门本身是否足够准确，而是为了把稳定子测量映射到真实器件，需要付出多大的输运和等待代价。

若以 $|0\rangle$ 与 $|1\rangle$ 表示同一离子的两个内部能级，并用 $\omega_0$ 表示两者之间的能级差，则单个离子的内部哈密顿量可以写为

$$
H_{\mathrm{int}} = \frac{\hbar \omega_0}{2} Z,
$$

其中 $Z$ 是计算子空间中的 pauli operator，$\hbar$ 是约化普朗克常数。离子并不是静止点粒子，而是在阱势中还具有量子化的振动自由度。若以 $a_m^\dagger$ 与 $a_m$ 分别表示第 $m$ 个振动模的产生与湮灭算符，以 $\omega_m$ 表示该振动模频率，则运动部分的哈密顿量可写为

$$
H_{\mathrm{mot}} = \sum_m \hbar \omega_m \left( a_m^\dagger a_m + \frac{1}{2} \right).
$$

因此，离子阱平台中的双比特门并不是直接由两个局域二能级之间的固定耦合给出，而是通过激光场或微波场把内部态与共享振动模耦合起来，再利用该共享振动模在多个离子之间传递相位和纠缠<sup>[1][2][4]</sup>。

在 Lamb-Dicke 近似下，若外部驱动场的有效 Rabi 频率为 $\Omega$，Lamb-Dicke 参数为 $\eta$，驱动失谐量为 $\delta$，则 Mølmer-Sørensen 门的相互作用哈密顿量可以写成

$$
H_{\mathrm{MS}} = \hbar \eta \Omega \left( a e^{- i \delta t} + a^\dagger e^{i \delta t} \right) S_\phi,
$$

其中 $a$ 与 $a^\dagger$ 表示所选公共振动模的湮灭和产生算符，$S_\phi = \sum_j \sigma_j^{\phi}$ 表示多个离子上的集体自旋算符，$\sigma_j^{\phi}$ 是第 $j$ 个离子在某一相位方向上的 pauli operator。这个表达式的意义在于，驱动场先把内部态信息映射到公共振动模，再在一个完整脉冲周期后把振动模解耦，只把所需的双比特几何相位保留在内部态上。若把门时间记为 $T_{2Q}$，则门结束后可得到形如

$$
U_{\mathrm{MS}} = \exp\!\left( - i \chi X_i X_j \right)
$$

的有效演化，其中 $\chi$ 是由驱动强度、失谐和脉冲时间共同决定的有效耦合角度。在适当单比特旋转配合下，这一门与 surface code 电路中常用的受控相位门属于 Clifford 等价类，因此可以作为稳定子提取的双比特纠缠基元<sup>[1][4][5]</sup>。

离子阱平台之所以适合 surface code，并不只是因为它能做高保真双比特门，而是因为它的门保真度和相干时间通常足以让人真正看见时序调度本身的成本。对于理想化的离子链，多个离子可通过共享振动模建立远距离耦合，这一点看起来比超导二维近邻结构更自由。但一旦进入真实可扩展架构，平台往往要采用 quantum charge-coupled device，也就是把离子分布在多个分区中，通过分裂、合并、穿结点和重新排列等方式把需要相互作用的离子送到同一操作区<sup>[3][6]</sup>。这意味着，连通性并不是没有代价的。每一次逻辑上简单的 ancilla-data 作用，在真实硬件上都可能伴随输运时间、重新冷却时间以及振动模重整过程。

单比特门在离子阱平台中通常通过共振微波或受激 Raman 脉冲完成。若记单比特门持续时间为 $T_{1Q}$，内部态能量弛豫时间为 $T_1$，相干时间为 $T_2$，则单比特门误差可以写成

$$
e_{1Q} \approx 1 - \exp\!\left( - a_1 \frac{T_{1Q}}{T_1} - b_1 \frac{T_{1Q}}{T_2} \right) + e_{\mathrm{ctrl},1Q},
$$

其中 $a_1$ 与 $b_1$ 是由脉冲方案决定的无量纲系数，$e_{\mathrm{ctrl},1Q}$ 表示激光强度漂移、相位噪声和失谐误差等控制误差贡献。由于超精细态或光学钟态的本征寿命极长，离子阱平台中的单比特门误差一般并不由能量弛豫主导，而更多由控制误差和残余退相位决定<sup>[1][2][4]</sup>。这也是为什么当前代码把 `p_gate_1q` 设为 $10^{-4}$ 量级，这一数值与近年高保真离子阱单比特操作的公开结果是相容的。

双比特门误差则来自更复杂的物理机制。若以 $T_{2Q}$ 表示 Mølmer-Sørensen 门时长，则其误差可以近似写成

$$
e_{2Q} \approx 1 - \exp\!\left( - a_2 \frac{T_{2Q}}{T_1} - b_2 \frac{T_{2Q}}{T_2} \right) + e_{\mathrm{mot}} + e_{\mathrm{ctrl},2Q},
$$

其中 $e_{\mathrm{mot}}$ 表示振动模加热、模频漂移和残余自旋-运动纠缠带来的误差，$e_{\mathrm{ctrl},2Q}$ 表示双光束不均匀性、光相位噪声和脉冲失配等控制误差。与中性原子平台不同，这里的难点不在于短寿命辅助态，而在于公共振动模是否能在门结束时真正回到解耦状态；与超导平台不同，这里的难点也不在于二维固定耦合图，而在于多离子系统中运动模工程是否仍然可控<sup>[1][4][5]</sup>。因此，离子阱平台虽然往往能给出极低的门误差，但双比特门的工程复杂度并未因此消失，只是以另一种形式表现出来。

测量通常通过状态依赖荧光完成。其基本原理是：对其中一个内部态施加近共振探测光，使其产生大量散射光子，而另一个态近似保持暗态，于是内部量子态被转化为可由光电探测器记录的亮暗差别<sup>[1][2]</sup>。若把测量时间记为 $T_{\mathrm{meas}}$，则测量误差一方面来自光子计数统计波动，另一方面来自串扰、探测效率有限和态准备误差。对 surface code 而言，真正重要的是，当辅助比特正在读出时，其余数据比特往往只能等待。因此，离子阱平台虽然有极长的本征相干时间，但一轮稳定子提取的总持续时间并不短，读出和输运阶段都会把大量物理时间转化为 idle 暴露窗口。

如果只考虑静止等待过程，令某个离子的等待时长为 $t_{\mathrm{idle}}$，则对应的有效等待误差可近似写为

$$
p_{\mathrm{idle}} \approx 1 - e^{- t_{\mathrm{idle}} / T_2}.
$$

当体系采用 QCCD 架构并允许离子在不同区域之间输运时，还需要把输运本身引入额外误差通道。若单次输运时间记为 $t_{\mathrm{tr}}$，输运引起的附加加热误差记为 $p_{\mathrm{heat}}$，则一次输运操作的总有效误差可近似写为

$$
p_{\mathrm{tr}} \approx 1 - \exp\!\left( - \frac{t_{\mathrm{tr}}}{T_2} \right) + p_{\mathrm{heat}}.
$$

这个公式表达了离子阱平台在当前 benchmark 中最关键的物理判断：即使 $T_2$ 很长，若单次输运时间达到毫秒量级，并且一轮稳定子提取中需要多次往返输运，那么最终累积的等待预算仍然不可忽略。当前项目的 trapped ion compiler 正是沿着这一逻辑实现的。它假定所有辅助比特位于区域 A，所有数据比特位于区域 B，每一次 ancilla-data 相互作用都必须经历“辅助比特输运到数据区、执行门、再输运回去”的过程，而且每次输运都对参与作用的两个比特施加由 `idle_noise()` 生成的等待噪声。

若把单次输运时间记为 $t_{\mathrm{transport}}$，单轮四个方向调度中的交互批次记为 $B$，每个 ancilla-data 对在每个批次中都需要一次来回输运，则单轮由输运主导的主要时间开销可以写成

$$
T_{\mathrm{transport,round}} \approx 2 B \, t_{\mathrm{transport}}.
$$

在当前代码中有 $B = 4$，`t_transport_ns = 2{,}000{,}000` 纳秒，也就是 $2$ 毫秒。于是仅输运部分就对应

$$
T_{\mathrm{transport,round}} \approx 2 \times 4 \times 2 \, \mathrm{ms} = 16 \, \mathrm{ms}.
$$

与此同时，编译器又把测量等待时间近似设为 `t_meas_ns = 0.9 \times t_cycle_ns`。若 `t_cycle_ns = 20{,}000{,}000` 纳秒，即 $20$ 毫秒，则测量等待时间约为 $18$ 毫秒。由此可以看出，当前代码下单轮真实暴露时间并不接近 $20$ 毫秒，而更接近“输运开销加测量等待开销”的更大数值。这说明离子阱平台与中性原子平台一样，在现有 benchmark 中存在“表征性单轮时间”和“按编译器逐步展开后的真实时序”不完全一致的问题。

若把各类物理误差合并成单轮等效物理错误率 $p_{\mathrm{eff}}$，则可写成

$$
p_{\mathrm{eff}} = c_1 e_{1Q} + c_2 e_{2Q} + c_3 e_{\mathrm{meas}} + c_4 e_{\mathrm{reset}} + c_5 p_{\mathrm{idle}} + c_6 p_{\mathrm{tr}},
$$

其中 $e_{\mathrm{meas}}$ 表示测量错误率，$e_{\mathrm{reset}}$ 表示复位错误率，$c_1,\dots,c_6$ 是由稳定子提取电路和调度结构决定的灵敏度系数。若物理平台工作在门槛以下，则逻辑错误率 $P_L$ 对码距 $d$ 的依赖仍可近似写成

$$
P_L \approx A \left( \frac{p_{\mathrm{eff}}}{p_{\mathrm{th}}} \right)^{\frac{d+1}{2}},
$$

其中 $A$ 是与具体电路结构相关的常数，$p_{\mathrm{th}}$ 表示容错门槛。对离子阱平台来说，这个表达式最重要的含义并不是“门越准越好”这样平凡的结论，而是指出：当平台已经拥有极高的门保真度后，进一步限制逻辑错误率的往往不再是 Clifford 门本身，而是输运、测量和读出等待所引入的长时间调度成本<sup>[3][6][7]</sup>。

因此，离子阱平台在三类硬件路线中的物理特征可以概括为如下命题。它拥有极高的单比特和双比特门保真度，也拥有远长于超导平台和中性原子 Rydberg 区的相干时间，因此在静态噪声层面非常有利；但一旦把 surface code 的重复局域稳定子提取映射到真实 QCCD 架构，就必须为输运、区域切换和读出等待支付明显的时间成本。也正因为如此，如果 benchmark 只保留门误差而忽略输运与等待，离子阱平台的逻辑表现会被显著高估；只有把这些时序过程显式纳入模型，平台的真实优势和真实瓶颈才会同时显现出来。

## 第二部分 官方数据整理与参数映射

若要把离子阱平台的公开数据导入当前 benchmark，需要先区分两类量。第一类是文献或厂商规格中较容易直接读取的量，如单比特门错误率、双比特门错误率、测量错误率以及相干时间。第二类则是为了让仿真闭环而不得不引入的工程参数，如复位误差、单次输运时间、输运加热项和单轮总周期时间。对离子阱平台而言，第二类量特别重要，因为 surface code 在真实器件上并不是简单地由“高保真门”自动推出，而是由门、输运和读出共同构成的整轮时序过程。

当前项目对离子阱平台使用的基础字段包括 `p_gate_1q`、`p_gate_2q`、`p_meas`、`p_reset`、`p_idle`、`cycle_time_us`、`T1_us` 和 `T2_us`。其中 `p_gate_1q`、`p_gate_2q` 和 `p_meas` 对应文献中最容易找到的门与读出错误率；`T1_us` 与 `T2_us` 对应长相干时间假设；`p_idle` 在 builtin 路径中只是一个聚合等待噪声；而 compiler 路径真正使用的关键附加参数则是 `t_transport_ns`、`t_cycle_ns` 和 `p_heating`。这意味着，对离子阱平台来说，builtin 与 compiler 的差别同样明显：前者是聚合噪声模型，后者则是显式输运模型。

根据 Quantinuum H2 的公开技术资料以及近年的高保真离子阱门和读出结果，可以把当前项目最关键的离子阱参考量整理为表 1。表中的“官方代表值”表示公开规格和代表性实验论文给出的典型量级；“当前代码值”表示仓库默认参数；“建议解释”则说明该量是可视为文献直接值，还是为了 benchmark 必须引入的工程估计。

| 参数 | 物理意义 | 官方代表值 | 当前代码值 | 建议解释 |
| --- | --- | --- | --- | --- |
| `p_gate_1q` | 单比特门错误率 | 约 $10^{-4}$ 量级<sup>[4][7]</sup> | $1.0 \times 10^{-4}$ | 与公开量级一致 |
| `p_gate_2q` | Mølmer-Sørensen 双比特门错误率 | 约 $10^{-3}$ 量级<sup>[5][7]</sup> | $1.0 \times 10^{-3}$ | 与公开量级一致 |
| `p_meas` | 测量错误率 | H2 官方 SPAM 指标约为 $(1.2$--$3.4) \times 10^{-3}$<sup>[8][9]</sup> | $6.0 \times 10^{-3}$ | 当前代码偏保守，高于官方均值 |
| `p_reset` | 复位误差 | 官方文档未单列 reset 概率 | $1.0 \times 10^{-3}$ | 当前 benchmark 工程估计 |
| `p_idle` | builtin 中每轮等待噪声 | H2 官方给出 depth-1 memory error 约 $(0.9$--$2.2) \times 10^{-4}$<sup>[9]</sup> | $1.0 \times 10^{-6}$ | 不是同一字段，但当前代码明显偏理想化 |
| `T1_us` | 能量弛豫时间 | 多秒量级以上<sup>[1][2]</sup> | $1.0 \times 10^{7}$ 微秒 | 代表长寿命近似 |
| `T2_us` | 相干时间 | 秒量级以上<sup>[1][2][3]</sup> | $1.0 \times 10^{7}$ 微秒 | 代表长相干近似 |
| `t_transport_ns` | 单次输运时间 | 毫秒量级<sup>[3][6]</sup> | $2{,}000{,}000$ 纳秒 | 编译器建模量 |
| `t_cycle_ns` | 单轮等效总时长 | 应由输运与读出共同决定 | $20{,}000{,}000$ 纳秒 | 编译器建模量 |
| `p_heating` | 输运附加加热误差 | 与具体器件和冷却流程相关 | $0.0$ | 当前先忽略的工程量 |

表 1 说明，当前项目对离子阱平台的基础门保真度口径总体上与公开代表值是一致的，而且在三类平台里它也是目前最容易被企业官方文档直接补强的一类：Quantinuum 的公开 validation 页面不仅给出单比特门误差、双比特门误差和 SPAM，还给出 leakage、mid-circuit measurement crosstalk 以及 depth-1 memory error 这类更接近真实运行成本的指标<sup>[8][9]</sup>。但这也暴露出另一层问题，即当前 benchmark 的 `p_idle = 10^{-6}` 显著低于官方 memory 指标所提示的 $10^{-4}$ 量级，而 `p_reset`、输运和整轮时间仍带有明显的工程汇总性质。尤其值得注意的是，`cycle_time_us = 10.0` 微秒只是一种基础表征，而 compiler 中真正决定离子等待暴露的 `t_transport_ns = 2` 毫秒和 `t_cycle_ns = 20` 毫秒则处在完全不同的时间尺度上。若再结合编译器的具体实现，单轮会经历四个方向批次，每一对 ancilla-data 相互作用都包含输运去程和回程，而读出阶段又附加了近似 $18$ 毫秒的数据等待。这意味着当前离子阱 benchmark 的真实主导量，不是微秒量级的门，而是毫秒量级的调度过程。

这些参数之间的关系可以写成更直接的形式。若以 $p$ 表示统一扫描中使用的双比特门错误率基准，则当前代码按固定比例令

$$
p_{1Q} = r_{1Q} p, \qquad p_{\mathrm{meas}} = r_{\mathrm{meas}} p, \qquad p_{\mathrm{reset}} = r_{\mathrm{reset}} p, \qquad p_{\mathrm{idle}} = r_{\mathrm{idle}} p,
$$

其中对离子阱默认参数有 $r_{1Q} = 0.1$，$r_{\mathrm{meas}} = 6.0$，$r_{\mathrm{reset}} = 1.0$，$r_{\mathrm{idle}} = 10^{-3}$。这意味着实验脚本显式传入统一的 $p$ 时，代码并不是认为所有误差通道相同，而是在保持离子阱平台内部误差结构不变的前提下，按双比特门错误率这一基准对整体噪声水平做缩放。这种做法有利于跨平台比较，但并不能替代某一具体器件的逐通道校准。

对 builtin 路径而言，项目直接把 `p_gate_2q`、`p_meas`、`p_reset` 和 `p_idle` 映射到 stim 的聚合噪声接口，因此它只能表达“离子阱平台在某种平均等待成本下的逻辑错误率趋势”。对 compiler 路径而言，项目则显式引入 QCCD 式分区和 ancilla 往返输运，并在每次输运时对参与的 ancilla 和 data 同时施加 idle 噪声，若后续启用 `p_heating`，还会额外叠加输运加热项。于是，compiler 模型能够表达一个对离子阱平台极其关键的事实，即当门保真度已经很高时，逻辑错误率是否继续下降，主要取决于整轮输运和读出的时间预算，而不是单个门还能否再优化一个小数量级。

因此，若后续要把官方数据更严格地导入本项目进行可信 benchmark，离子阱平台至少需要完成三项修正。第一，应把 `p_reset` 的来源明确为具体的态制备和再初始化流程，而不是只保留一个抽象概率。第二，应统一 `cycle_time_us`、`t_cycle_ns` 与按编译器逐步展开后的整轮时间三者之间的关系，使 builtin 与 compiler 至少对应同一类物理节奏。第三，应进一步决定 `p_heating` 是否保持为零，还是依据公开输运实验给出一个非零代表值，从而避免在长输运情形下低估振动模工程的真实成本。若这些校准被补齐，则离子阱平台的 benchmark 才能既体现其高保真门优势，又不掩盖其扩展到表面码时真正要面对的输运代价。

## 综述部分参考文献

[1] D. Leibfried, R. Blatt, C. Monroe, and D. Wineland, Quantum dynamics of single trapped ions, Reviews of Modern Physics 75, 281-324, 2003.

[2] H. Häffner, C. F. Roos, and R. Blatt, Quantum computing with trapped ions, Physics Reports 469, 155-203, 2008.

[3] C. Monroe, W. C. Campbell, L.-M. Duan, Z.-X. Gong, A. V. Gorshkov, P. W. Hess, R. Islam, K. Kim, N. M. Linke, G. Pagano, P. Richerme, C. Senko, and N. Y. Yao, Programmable quantum simulations of spin systems with trapped ions, Reviews of Modern Physics 93, 025001, 2021.

[4] K. A. Landsman et al., Two-qubit entangling gates within arbitrarily long chains of trapped ions, Physical Review A 100, 022332, 2019.

[5] T. P. Harty et al., High-fidelity preparation, gates, memory, and readout of a trapped-ion quantum bit, Physical Review Letters 113, 220501, 2014.

[6] D. Kielpinski, C. Monroe, and D. J. Wineland, Architecture for a large-scale ion-trap quantum computer, Nature 417, 709-711, 2002.

[7] J. M. Pino et al., Demonstration of the trapped-ion quantum CCD computer architecture, Nature 592, 209-213, 2021.

[8] Quantinuum, System Model H2, official hardware page, https://www.quantinuum.com/hardware/h2, accessed 2026-06-11.

[9] Quantinuum Systems Documentation, Performance Validation, including System Model H2 Product Data Sheet and component benchmarks, https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/performance_validation.html, accessed 2026-06-11.

## 数据部分参考文献

[D1] Quantinuum, System Model H2 Product Data Sheet, official data sheet linked from Quantinuum documentation, https://docs.quantinuum.com/systems/_static/assets/data_sheets/Quantinuum%20H2%20Product%20Data%20Sheet.pdf, accessed 2026-06-11.

[D2] Quantinuum Systems Documentation, Performance Validation, including System Model H2 Product Data Sheet and component benchmarks, https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/performance_validation.html, accessed 2026-06-11.

[D3] J. M. Pino et al., Demonstration of the trapped-ion quantum CCD computer architecture, Nature 592, 209-213, 2021.