

## 1 为什么量子力学需要复向量空间

### 1.1 量子信息的载体

在量子信息理论中，我们不再首先关注物质、能量或波动图像，而是关注**信息、概率、可观测量的关系**。量子态由复向量空间中的矢量表示，概率则与矢量分量的模方相联系。这要求我们先建立复向量空间的严格数学框架。

---

## 2 Dirac符号与向量空间公理

### 2.1 Ket矢量与向量空间

在量子力学中，复向量空间的元素记为 $|a\rangle$，称为 **ket（右矢）** 或 **ket-向量**。一个复向量空间 $\mathcal{H}$ 满足以下公理：

**公理 1（加法封闭性）**：对任意 $|a\rangle, |b\rangle \in \mathcal{H}$，其和 $|a\rangle + |b\rangle = |c\rangle$ 仍属于 $\mathcal{H}$。

**公理 2（交换律）**：
$$
|a\rangle + |b\rangle = |b\rangle + |a\rangle
$$

**公理 3（结合律）**：
$$
(|a\rangle + |b\rangle) + |c\rangle = |a\rangle + (|b\rangle + |c\rangle)
$$

**公理 4（零元存在）**：存在唯一的零向量 $|0\rangle$，使得对任意 $|a\rangle$：
$$
|a\rangle + |0\rangle = |a\rangle
$$

**公理 5（逆元存在）**：对任意 $|a\rangle$，存在唯一的 $-|a\rangle$，使得：
$$
|a\rangle + (-|a\rangle) = |0\rangle
$$

以上五条公理与普通实向量空间无异。量子力学区别于经典力学的关键在于以下两条涉及**复数标量乘法**的公理：

**公理 6（数乘封闭性与线性性）**：对任意 $|a\rangle \in \mathcal{H}$ 和任意复数 $\zeta \in \mathbb{C}$，数乘 $\zeta|a\rangle \equiv |\zeta a\rangle$ 仍属于 $\mathcal{H}$，且满足分配律：
$$
\zeta(|a\rangle + |b\rangle) = \zeta|a\rangle + \zeta|b\rangle, \quad (\zeta + \omega)|a\rangle = \zeta|a\rangle + \omega|a\rangle
$$

> **物理诠释**：复数标量乘法对应于量子态的整体相位变换。若 $|\psi'\rangle = e^{i\phi}|\psi\rangle$，则 $|\psi'\rangle$ 与 $|\psi\rangle$ 代表同一物理状态，因为可观测概率仅依赖于模方。

### 2.2 对偶空间与Bra矢量

每一个复向量空间都存在一个**对偶空间（dual space）**。对每一个 ket $|a\rangle$，在对偶空间中存在一个对应的 **bra（左矢）** $\langle a|$。bra 满足与 ket 相同的线性结构，但数乘规则不同：

> **关键性质**：与 ket $|\zeta a\rangle$ 对应的 bra 为
> $$ \langle \zeta a| = \zeta^* \langle a|  $$
> 即复数标量在转为对偶空间时取**复共轭**。

这一性质保证了内积的厄米性，是量子力学概率诠释的数学根基。

---

## 3 内积、归一化与正交性

### 3.1 内积的定义与性质

bra 与 ket 的配对 $\langle b|a\rangle$ 构成一个**复数**，称为内积（inner product）。它是经典点积在复空间的推广，满足：

1. **对 ket 右线性**：
   $$
   \langle c|(|a\rangle + |b\rangle) = \langle c|a\rangle + \langle c|b\rangle
   $$

2. **对 bra 左线性**：
   $$
   (\langle a| + \langle b|)|c\rangle = \langle a|c\rangle + \langle b|c\rangle
   $$

3. **共轭对称性**：
   $$
   \langle b|a\rangle = \langle a|b\rangle^*
   $$

由性质 3 立即可得 $\langle a|a\rangle$ 必为**实数**（因为 $\langle a|a\rangle = \langle a|a\rangle^*$）。

### 3.2 矩阵表示下的内积

若将 ket 表示为列向量：
$$
|a\rangle = \begin{pmatrix} \alpha_1 \\ \alpha_2 \\ \vdots \\ \alpha_n \end{pmatrix}, \quad |b\rangle = \begin{pmatrix} \beta_1 \\ \beta_2 \\ \vdots \\ \beta_n \end{pmatrix}
$$

则对应的 bra 为行向量的厄米共轭（转置并取复共轭）：
$$
\langle b| = \begin{pmatrix} \beta_1^* & \beta_2^* & \cdots & \beta_n^* \end{pmatrix}
$$

内积即矩阵乘法：
$$
\langle b|a\rangle = \sum_{i=1}^n \beta_i^* \alpha_i
$$

验证共轭对称性：
$$
\langle a|b\rangle = \sum_i \alpha_i^* \beta_i = \left(\sum_i \beta_i^* \alpha_i\right)^* = \langle b|a\rangle^*
$$

### 3.3 归一化与正交

> **定义（归一化向量）**：若 $\langle a|a\rangle = 1$，则称 $|a\rangle$ 为**归一化向量**。

> **定义（正交）**：若 $\langle b|a\rangle = 0$，则称 $|a\rangle$ 与 $|b\rangle$ **正交**。

归一化条件对应于概率守恒：量子态的总概率必须为1。正交性则对应于互斥的物理状态——若系统处于 $|a\rangle$，则测得 $|b\rangle$ 的概率为零。

---

## 4 标准正交基与完备性关系

### 4.1 线性无关与基

向量集合 $\{|x_1\rangle, |x_2\rangle, \ldots, |x_n\rangle\}$ 称为**线性无关**，如果方程
$$
\sum_{i=1}^n \eta_i |x_i\rangle = |0\rangle
$$
的唯一解是 $\eta_i = 0$（对所有 $i$）。若存在非零解，则称该集合**线性相关**。

$n$ 个线性无关的向量构成 $n$ 维复向量空间 $\mathbb{C}^n$ 的一组**基（basis）**。例如：
$$
\mathsf{v}_1 = \begin{pmatrix} 2 \\ 0 \end{pmatrix}, \quad \mathsf{v}_2 = \begin{pmatrix} 1 \\ -1 \end{pmatrix}
$$
构成 $\mathbb{C}^2$ 的一组基，但它们既不正交也未归一化。

### 4.2 标准正交基

在量子力学中，我们优先选用**标准正交基（orthonormal basis）** $\{|i\rangle\}_{i=1}^N$，满足：
$$
\langle i|j\rangle = \delta_{ij} = \begin{cases} 1, & i=j \\ 0, & i \neq j \end{cases}
$$

任意向量 $|a\rangle$ 可按基展开：
$$
|a\rangle = \sum_i \alpha_i |i\rangle
$$

利用标准正交性，第 $j$ 个分量可通过内积提取：
$$
\alpha_j = \langle j|a\rangle
$$

证明：将展开式两边左乘 $\langle j|$：
$$
\langle j|a\rangle = \sum_i \alpha_i \langle j|i\rangle = \sum_i \alpha_i \delta_{ji} = \alpha_j
$$

### 4.3 完备性关系

将分量表达式代回展开式：
$$
|a\rangle = \sum_i |i\rangle \langle i|a\rangle
$$

由于 $|a\rangle$ 任意，我们得到算符等式：

> **定理（完备性关系）**：对于标准正交基 $\{|i\rangle\}$，
> $$ \sum_{i=1}^N |i\rangle\langle i| = \hat{I}$$
> 其中 $\hat{I}$ 为恒等算符。

**物理诠释**：完备性关系表明，所有正交基矢对应的投影之和覆盖了完整的向量空间。在量子测量理论中，这对应于所有可能测量结果的概率之和为1。

---

## 5 投影算符

### 5.1 定义与作用

> **定义（投影算符）**：沿基矢 $|k\rangle$ 方向的投影算符定义为
> $$\hat{P}_k \equiv |k\rangle\langle k|$$

$\hat{P}_k$ 作用于任意向量 $|v\rangle$ 的效果为：
$$
\hat{P}_k |v\rangle = |k\rangle\langle k|v\rangle = (\langle k|v\rangle) |k\rangle
$$

即提取 $|v\rangle$ 在 $|k\rangle$ 方向的分量，并将其映射到平行于 $|k\rangle$ 的向量。剩余部分 $|v\rangle - \hat{P}_k|v\rangle$ 与 $|k\rangle$ 正交：
$$
\langle k|(|v\rangle - \hat{P}_k|v\rangle) = \langle k|v\rangle - \langle k|k\rangle\langle k|v\rangle = 0
$$

### 5.2 投影算符的代数性质

投影算符集合 $\{\hat{P}_k = |k\rangle\langle k|\}$ 满足以下关键性质：

**性质 1（幂等性）**：
$$
\hat{P}_k^2 = (|k\rangle\langle k|)(|k\rangle\langle k|) = |k\rangle(\langle k|k\rangle)\langle k| = |k\rangle\langle k| = \hat{P}_k
$$
这反映了"投影一次后再投影一次结果不变"的几何直观。

**性质 2（正交性）**：
$$
\hat{P}_k \hat{P}_j = |k\rangle\langle k|j\rangle\langle j| = |k\rangle\delta_{kj}\langle j| = 0 \quad (k \neq j)
$$
不同方向的投影互不相容。

**性质 3（完备性）**：
$$
\sum_k \hat{P}_k = \sum_k |k\rangle\langle k| = \hat{I}
$$
这正是上一节完备性关系的算符形式。

> **物理诠释**：在量子测量中，$\hat{P}_k$ 对应于测得本征态 $|k\rangle$ 这一事件。幂等性表示重复测量同一性质得到相同结果；正交性表示不同本征态互斥；完备性表示所有可能结果的概率总和为1。

---
