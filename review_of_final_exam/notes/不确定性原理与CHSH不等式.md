
## 0. 概述
**不确定性原理**：
$$
\Delta A \Delta B \geq \frac{1}{2}|\langle[\hat{A}, \hat{B}]\rangle|
$$


---

## 1 不确定性原理的严格推导

### 1.1 问题与定义

量子力学中，若两个可观测量 $\hat{A}$ 和 $\hat{B}$ 不对易，则它们无法同时拥有确定值。我们定量刻画这种限制。

> **定义（不确定度）**：可观测量 $\hat{A}$ 在态 $|\psi\rangle$ 中的不确定度为
> $$\Delta A \equiv \sqrt{\langle \hat{A}^2 \rangle - \langle \hat{A} \rangle^2} = \sqrt{\langle\psi|(\hat{A} - \langle\hat{A}\rangle)^2|\psi\rangle}$$

### 1.2 Cauchy-Schwarz不等式的应用

> **定理（广义不确定性原理）**：对任意态 $|\psi\rangle$ 和任意两个厄米算符 $\hat{A}, \hat{B}$，
> $$\Delta A \Delta B \geq \frac{1}{2}|\langle[\hat{A}, \hat{B}]\rangle|$$

**证明**：

定义中心化的算符 $\delta\hat{A} \equiv \hat{A} - \langle\hat{A}\rangle\hat{I}$，$\delta\hat{B} \equiv \hat{B} - \langle\hat{B}\rangle\hat{I}$。构造两个辅助态：
$$
|\phi_1\rangle \equiv \delta\hat{A}|\psi\rangle, \quad |\phi_2\rangle \equiv \delta\hat{B}|\psi\rangle
$$

Cauchy-Schwarz 不等式给出：
$$
|\langle\phi_1|\phi_2\rangle|^2 \leq \langle\phi_1|\phi_1\rangle \langle\phi_2|\phi_2\rangle
$$

计算各项：
$$
\langle\phi_1|\phi_1\rangle = \langle\psi|(\delta\hat{A})^\dagger(\delta\hat{A})|\psi\rangle = \langle\psi|(\delta\hat{A})^2|\psi\rangle = (\Delta A)^2
$$
（同理 $\langle\phi_2|\phi_2\rangle = (\Delta B)^2$）

计算内积：
$$
\langle\phi_1|\phi_2\rangle = \langle\psi|\delta\hat{A}\delta\hat{B}|\psi\rangle
$$

将乘积分解为对称与反对称部分：
$$
\delta\hat{A}\delta\hat{B} = \frac{1}{2}\{\delta\hat{A}, \delta\hat{B}\} + \frac{1}{2}[\delta\hat{A}, \delta\hat{B}]
$$

其中 $\{\cdot,\cdot\}$ 为反对易子（厄米），$[\cdot,\cdot]$ 为对易子（反厄米）。取期望值：
- $\langle\{\delta\hat{A}, \delta\hat{B}\}\rangle$ 为实数
- $\langle[\delta\hat{A}, \delta\hat{B}]\rangle = \langle[\hat{A}, \hat{B}]\rangle$ 为纯虚数（因 $[\hat{A},\hat{B}]$ 反厄米）

因此 $\langle\phi_1|\phi_2\rangle$ 是复数，其实部来自反对易子，虚部来自对易子。取模方：
$$
|\langle\phi_1|\phi_2\rangle|^2 = \left|\frac{1}{2}\langle\{\delta\hat{A}, \delta\hat{B}\}\rangle\right|^2 + \left|\frac{1}{2}\langle[\hat{A}, \hat{B}]\rangle\right|^2 \geq \frac{1}{4}|\langle[\hat{A}, \hat{B}]\rangle|^2
$$

代回 Cauchy-Schwarz 不等式：
$$
(\Delta A)^2 (\Delta B)^2 \geq \frac{1}{4}|\langle[\hat{A}, \hat{B}]\rangle|^2
$$

开方即得：
$$
\Delta A \Delta B \geq \frac{1}{2}|\langle[\hat{A}, \hat{B}]\rangle|
$$

### 1.3 典型实例

对位置 $\hat{x}$ 与动量 $\hat{p}_x = -i\hbar \frac{\partial}{\partial x}$，对易关系 $[\hat{x}, \hat{p}_x] = i\hbar$，故：
$$
\Delta x \Delta p_x \geq \frac{\hbar}{2}
$$

对自旋分量 $[\hat{\sigma}_x, \hat{\sigma}_y] = 2i\hat{\sigma}_z$（由Pauli矩阵代数），故：
$$
\Delta \sigma_x \Delta \sigma_y \geq |\langle\hat{\sigma}_z\rangle|
$$

---

## 2 CHSH游戏：经典与量子的对决

### 2.1 游戏规则

CHSH（Clauser-Horne-Shimony-Holt）游戏是一种**非局域游戏（nonlocal game）**，用于检验物理关联的经典极限。

**参与者**：Alice、Bob（两位玩家），一位裁判（Referee）。
**流程**：
1. 裁判随机生成两个问题比特 $r, s \in \{0,1\}$，分别发送给 Alice 和 Bob。
2. Alice 根据 $r$ 回答一个比特 $a$；Bob 根据 $s$ 回答一个比特 $b$。
3. 获胜条件：
   $$
   a \oplus b = r \cdot s
   $$
   即：
   - $(r,s) = (0,0)$：需 $a \oplus b = 0$
   - $(r,s) = (0,1)$：需 $a \oplus b = 0$
   - $(r,s) = (1,0)$：需 $a \oplus b = 0$
   - $(r,s) = (1,1)$：需 $a \oplus b = 1$

**限制**：Alice 和 Bob 在游戏过程中不能互相通信（空间上可分离）。他们可以在游戏前商定策略，甚至可以共享经典随机变量（局域隐变量）。

### 2.2 经典策略的极限

考虑**确定性策略**：Alice 的策略是函数 $a(r)$，Bob 的策略是函数 $b(s)$。四个获胜条件要求：
$$
\begin{cases}
a(0) \oplus b(0) = 0 \\
a(0) \oplus b(1) = 0 \\
a(1) \oplus b(0) = 0 \\
a(1) \oplus b(1) = 1
\end{cases}
$$

将四个方程模2相加（即异或运算）：
$$
\text{左边} = [a(0)+b(0)+a(0)+b(1)+a(1)+b(0)+a(1)+b(1)] \mod 2 = 0
$$
（因为每个 $a(\cdot)$ 和 $b(\cdot)$ 出现两次，$2x \equiv 0 \mod 2$）

$$
\text{右边} = 0 + 0 + 0 + 1 = 1
$$

得到 $0 = 1$，矛盾！因此**不存在能同时满足四个条件的确定性经典策略**。

由于四个问题等概率出现，确定性策略最多满足其中3个，故最高胜率：
$$
\mathrm{P}_{\mathrm{win}}^{\mathrm{classical}} \leq \frac{3}{4} = 75\%
$$

概率性策略（共享随机数）也无法突破此极限，这是**CHSH不等式**（一种 Bell 不等式）的内容。

### 2.3 量子策略：纠缠的力量

若 Alice 和 Bob 在游戏前共享一个纠缠态（例如单态 $|\Psi_-\rangle = \frac{1}{\sqrt{2}}(|01\rangle - |10\rangle)$），并根据各自的问题选择不同的测量基，则可通过量子关联提高胜率。

**标准量子策略**：
- **Alice**：
  - 若 $r=0$，测量 $\hat{\sigma}_z$（基 $|0\rangle, |1\rangle$）
  - 若 $r=1$，测量 $\hat{\sigma}_x$（基 $|+\rangle, |-\rangle$）
- **Bob**：
  - 若 $s=0$，测量沿 $(\hat{\sigma}_z + \hat{\sigma}_x)/\sqrt{2}$ 方向的自旋
  - 若 $s=1$，测量沿 $(\hat{\sigma}_z - \hat{\sigma}_x)/\sqrt{2}$ 方向的自旋

测量结果 $+1$ 映射为回答 $0$，$-1$ 映射为回答 $1$（或适当调整）。通过计算各问题组合下的关联函数，可得量子策略的胜率为：

$$
\mathrm{P}_{\mathrm{win}}^{\mathrm{quantum}} = \cos^2\frac{\pi}{8} \approx 0.8536 > 0.75
$$

### 2.4 Bell不等式的违反与物理意义

CHSH 不等式将经典关联（包括所有局域隐变量理论）的获胜概率限制在 $75\%$ 以下。量子力学预言约 $85.36\%$，实验上（如 1972 年 Clauser 的实验、后续 Aspect 实验等）反复验证了这一违反。

> **核心结论**：CHSH 游戏的分析表明，量子纠缠产生的关联无法由任何局域隐变量理论复现。这种"非经典关联"并非超光速通信，而是量子态空间结构的内在特征。它既是量子力学完备性的有力证据，也是量子信息科学（量子密钥分发、量子计算）的核心资源。

> **小结**：从不确定性原理的严格推导到 CHSH 游戏中量子对经典的超越，我们看到了量子力学在数学结构上的自洽性与在物理预言上的非凡性。不确定性原理限制了共轭变量的同时精度，而 Bell 不等式的违反则证明了量子关联的本质非局域性——两者共同构成了量子信息理论的物理基石。