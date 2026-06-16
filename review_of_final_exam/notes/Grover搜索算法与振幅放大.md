
## 1 非结构化搜索问题

### 1.1 问题设定

> **定义（Grover搜索问题）**：给定一个包含 $N = 2^n$ 个元素的无序数据库，其中恰好有一个目标元素标记为 $a$。我们拥有一个黑箱 Oracle，可以判断任意元素 $x$ 是否为目标：
> $$f(x) = \begin{cases} 1, & x = a, \\ 0, & x \neq a. \end{cases}$$
> 目标是以尽可能少的查询次数找到 $a$。

**经典复杂度**：在最坏情况下需检查全部 $N$ 个元素；平均而言需 $N/2$ 次查询。经典算法的时间复杂度为 $O(N)$。

**量子目标**：利用量子叠加与干涉，实现低于线性时间的加速。

---

## 2 Oracle的量子实现与相位反冲

### 2.1 量子Oracle的幺正形式

与Deutsch问题类似，将Oracle嵌入双寄存器幺正算符：

$$\hat{U}_f|x\rangle|y\rangle = |x\rangle|y \oplus f(x)\rangle.$$

### 2.2 相位Oracle的构造

将辅助输出比特初始化为 $|-\rangle = \hat{H}|1\rangle = \frac{1}{\sqrt{2}}(|0\rangle-|1\rangle)$。则

$$\hat{U}_f|x\rangle|-\rangle = (-1)^{f(x)}|x\rangle|-\rangle.$$

**物理诠释**：当 $x=a$ 时，辅助比特拾取一个负号；当 $x\neq a$ 时，保持不变。由于辅助比特始终处于 $|-\rangle$，它在整个算法中不被测量，仅作为相位反冲的媒介。

因此，Oracle在 $n$ 比特输入空间的作用等价于：

> **相位Oracle**：
> $$\hat{V} = \hat{I} - 2|a\rangle\langle a| = \sum_{x=0}^{N-1}(-1)^{f(x)}|x\rangle\langle x|.$$

**验证**：$\hat{V}|a\rangle = -|a\rangle$；对任意 $|x\rangle \perp |a\rangle$，$\hat{V}|x\rangle = |x\rangle$。$\hat{V}$ 是关于超平面正交于 $|a\rangle$ 的**反射**（更准确地，是反转 $|a\rangle$ 分量的符号）。

---

## 3 几何图像：二维子空间中的旋转

### 3.1 态空间的约化

Grover算法的全部动力学可约化到由两个态张成的二维实平面：
- **目标态** $|a\rangle$；
- **均匀叠加态** $|\phi\rangle = \hat{H}^{\otimes n}|0\rangle^{\otimes n} = \frac{1}{\sqrt{N}}\sum_{x=0}^{N-1}|x\rangle$。

定义 $|a_\perp\rangle$ 为与 $|a\rangle$ 正交且位于 $\text{span}\{|a\rangle, |\phi\rangle\}$ 内的单位矢量。将 $|\phi\rangle$ 在此基下分解：

$$|\phi\rangle = \cos\theta\,|a_\perp\rangle + \sin\theta\,|a\rangle,$$

其中

$$\sin\theta = \langle a|\phi\rangle = \frac{1}{\sqrt{N}}, \quad \cos\theta = \sqrt{1-\frac{1}{N}}.$$

对于大 $N$，$\theta \approx 1/\sqrt{N}$。

### 3.2 两个反射算符

> **定义（目标反射）**：
> $$\hat{V} = \hat{I} - 2|a\rangle\langle a|.$$
> 几何作用：保持 $|a_\perp\rangle$ 不变，反转 $|a\rangle$ 的符号，即关于 $|a_\perp\rangle$ 方向的**反射**。

> **定义（均匀态反射）**：
> $$\hat{W} = 2|\phi\rangle\langle\phi| - \hat{I}.$$
> 几何作用：保持 $|\phi\rangle$ 不变，反转其正交补方向的符号，即关于 $|\phi\rangle$ 方向的**反射**。

### 3.3 反射复合=旋转的严格证明

在二维子空间 $\{|a_\perp\rangle, |a\rangle\}$ 中，取矩阵表示：
- $|a_\perp\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}$，$|a\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$。

则
$$\hat{V} = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}.$$

对于 $\hat{W}$，利用 $|\phi\rangle = \begin{pmatrix} \cos\theta \\ \sin\theta \end{pmatrix}$：

$$|\phi\rangle\langle\phi| = \begin{pmatrix} \cos^2\theta & \cos\theta\sin\theta \\ \cos\theta\sin\theta & \sin^2\theta \end{pmatrix},$$

$$\hat{W} = 2|\phi\rangle\langle\phi| - I = \begin{pmatrix} 2\cos^2\theta-1 & 2\cos\theta\sin\theta \\ 2\cos\theta\sin\theta & 2\sin^2\theta-1 \end{pmatrix} = \begin{pmatrix} \cos 2\theta & \sin 2\theta \\ \sin 2\theta & -\cos 2\theta \end{pmatrix}.$$

这是关于方向角 $\theta$ 的反射矩阵。计算复合作用：

$$\hat{W}\hat{V} = \begin{pmatrix} \cos 2\theta & \sin 2\theta \\ \sin 2\theta & -\cos 2\theta \end{pmatrix}\begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix} = \begin{pmatrix} \cos 2\theta & -\sin 2\theta \\ \sin 2\theta & \cos 2\theta \end{pmatrix}.$$

> **结论**：$\hat{W}\hat{V}$ 是二维平面上的**旋转矩阵**，将任意矢量向 $|a\rangle$ 方向旋转角度 $2\theta$。

### 3.4 迭代过程

初始态为 $|\phi\rangle$，与 $|a_\perp\rangle$ 的夹角为 $\theta$。每次施加一次 Grover 迭代 $\hat{G} = \hat{W}\hat{V}$：
- 第 1 次后：夹角变为 $\theta + 2\theta = 3\theta$；
- 第 $k$ 次后：夹角变为 $(2k+1)\theta$。

目标是使态矢量尽可能对准 $|a\rangle$，即夹角接近 $\pi/2$。因此选择迭代次数 $k$ 满足

$$(2k+1)\theta \approx \frac{\pi}{2} \quad\Rightarrow\quad k \approx \frac{\pi}{4\theta} - \frac{1}{2}.$$

代入 $\theta \approx \arcsin(1/\sqrt{N}) \approx 1/\sqrt{N}$（大 $N$ 极限）：

> **Grover算法复杂度**：
> $$k \approx \frac{\pi}{4}\sqrt{N} = O(\sqrt{N}).$$

**误差分析**：由于 $k$ 必须为整数，最终角度误差不超过 $\theta \sim 1/\sqrt{N}$。测量得到 $|a\rangle$ 的概率为 $\sin^2\big((2k+1)\theta\big) \approx 1 - O(1/N)$，极高。若需确保成功，可重复整个协议数次。

---

## 4 反射算符的电路实现

### 4.1 均匀态反射的分解

$$\hat{W} = \hat{H}^{\otimes n}\big(2|0\ldots0\rangle\langle 0\ldots0| - \hat{I}\big)\hat{H}^{\otimes n} \equiv \hat{H}^{\otimes n}\hat{W}'\hat{H}^{\otimes n}.$$

由于 $\hat{H}^{\otimes n}$ 是自逆的，问题转化为实现 $\hat{W}'$。

### 4.2 零态条件相位门

$\hat{W}'$ 的作用为：翻转全零态 $|0\ldots0\rangle$ 的符号，其余基态不变：

$$\hat{W}'|x\rangle = \begin{cases} -|0\ldots0\rangle, & x=0, \\ |x\rangle, & x\neq 0. \end{cases}$$

> **实现**：
> $$\hat{W}' = \hat{X}^{\otimes n}\big(\hat{C}^{n-1}\hat{Z}\big)\hat{X}^{\otimes n},$$
> 其中 $\hat{C}^{n-1}\hat{Z}$ 为 $(n-1)$-控制 $\hat{Z}$ 门（即 $n$ 比特门，当且仅当前 $n-1$ 个控制位均为 $|1\rangle$ 时，对第 $n$ 个目标位施加 $\hat{Z}$）。

**验证**：$\hat{X}^{\otimes n}|0\ldots0\rangle = |1\ldots1\rangle$；$\hat{C}^{n-1}\hat{Z}$ 在 $|1\ldots1\rangle$ 上作用为 $-|1\ldots1\rangle$（因所有控制条件满足，目标位相位翻转）；再经 $\hat{X}^{\otimes n}$ 回到 $-|0\ldots0\rangle$。对任何非零基态，经 $\hat{X}^{\otimes n}$ 后至少有一个控制位为 $|0\rangle$，$\hat{C}^{n-1}\hat{Z}$ 不作用，最终不变。

---

## 5 量子优越性（Quantum Supremacy）

### 5.1 从算法到实验里程碑

Grover算法展示了量子计算相对于经典计算的**多项式级加速**（二次加速）。然而，量子计算的终极愿景是实现**指数级加速**或解决经典计算机无法模拟的问题。

> **定义（量子优越性）**：由 John Preskill 提出，指量子设备在特定计算任务上展现出超越任何已知经典算法或现有经典超级计算机的能力。该任务本身未必具有实际应用价值，但其完成标志着量子计算硬件与操控技术达到关键门槛。

### 5.2 随机电路采样与扩展丘奇-图灵论题

一个典型的优越性实验任务是**随机电路采样（Random Circuit Sampling）**：对由随机单比特门和双比特门构成的深度量子电路，采样其输出分布。

- **经典模拟**：精确模拟 $n$ 量子比特的随机电路需要存储 $2^n$ 个复振幅，内存需求随比特数指数增长。当前经典极限约为 50 量子比特。
- **实验进展**：2019 年，Google 团队利用 53 量子比特 Sycamore 处理器在约 200 秒内完成了随机电路采样，而估计当时最强经典超级计算机需数千年。

> **理论意义**：量子优越性实验反驳了**扩展丘奇-图灵论题**（即任何有效算法过程均可被概率图灵机有效模拟），支持**量子扩展丘奇-图灵论题**——量子计算机可有效模拟任何物理过程。

---
