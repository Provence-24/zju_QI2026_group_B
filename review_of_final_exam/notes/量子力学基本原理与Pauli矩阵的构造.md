
## 1 量子力学的五条基本原理

量子力学的数学框架可由以下五条基本原理概括：

> **原理 1（态空间）**：系统的状态由复向量空间中的向量（态矢）表示。
>
> **原理 2（可观测量）**：物理可观测量由线性算符表示。
>
> **原理 3（测量结果）**：单次测量的可能结果是对应算符的本征值。
>
> **原理 4（可区分性）**：明确可区分的量子态由互相正交的向量表示。
>
> **原理 5（Born规则）**：若系统处于态 $|\psi\rangle$，测量可观测量 $\hat{L}$ 得到本征值 $\lambda$ 的概率为
> $$  \mathrm{P}_\lambda = |\langle\lambda|\psi\rangle|^2 = \langle\psi|\lambda\rangle\langle\lambda|\psi\rangle \equiv \langle\psi|\hat{P}_\lambda|\psi\rangle $$
> 测量后，系统坍缩到对应的本征态 $|\lambda\rangle$。

以下我们将这些原理应用于自旋 $1/2$ 系统，从第一性原理构造Pauli矩阵。

---

## 2 构造 $\hat{\sigma}_z$：从本征值到矩阵形式


自旋 $z$ 分量是一个可观测量，由厄米算符 $\hat{\sigma}_z$ 表示。实验告诉我们，测量 $z$ 方向自旋只能得到两个结果，约定为 $\pm 1$（任何比例因子可吸收到算符定义中）。因此 $\hat{\sigma}_z$ 有两个本征值 $+1$ 和 $-1$，对应本征态 $|0\rangle$（自旋向上）和 $|1\rangle$（自旋向下）：

$$
\hat{\sigma}_z|0\rangle = +1|0\rangle, \quad \hat{\sigma}_z|1\rangle = -1|1\rangle
$$

$|0\rangle$ 与 $|1\rangle$ 代表明确可区分的测量结果，因此它们必须正交：
$$
\langle 0|1\rangle = 0
$$

结合归一化 $\langle 0|0\rangle = \langle 1|1\rangle = 1$，$\{|0\rangle, |1\rangle\}$ 构成 $\mathbb{C}^2$ 的标准正交基。


算符 $\hat{\sigma}_z$ 在自身本征基下的矩阵元为：
$$
(\sigma_z)_{kj} = \langle k|\hat{\sigma}_z|j\rangle
$$

具体计算：
- $\langle 0|\hat{\sigma}_z|0\rangle = \langle 0|(+1|0\rangle) = +1$
- $\langle 0|\hat{\sigma}_z|1\rangle = \langle 0|(-1|1\rangle) = -\langle 0|1\rangle = 0$
- $\langle 1|\hat{\sigma}_z|0\rangle = \langle 1|(+1|0\rangle) = +\langle 1|0\rangle = 0$
- $\langle 1|\hat{\sigma}_z|1\rangle = \langle 1|(-1|1\rangle) = -1$

因此：
$$
\sigma_z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}
$$

---

## 3 构造 $\hat{\sigma}_x$：从实验数据到本征态

### 3.1 实验事实

考虑沿 $x$ 方向的 Stern-Gerlach 装置。它测量自旋 $x$ 分量，本征值同样为 $\pm 1$，对应本征态记为 $|r\rangle$（右，right，对应 $+1$）和 $|l\rangle$（左，left，对应 $-1$）。

**关键实验**：将银原子通过 $x$ 方向装置筛选出 $|r\rangle$ 态，再让其通过 $z$ 方向装置。实验发现原子束分裂为两束，**强度相等**。

这意味着 $|r\rangle$ 在 $z$ 基下展开时，两个基态的概率必须相等：
$$
|\langle 0|r\rangle|^2 = |\langle 1|r\rangle|^2 = \frac{1}{2}
$$

### 3.2 本征态的确定

由上述条件，设：
$$
|r\rangle = \frac{1}{\sqrt{2}}|0\rangle + \frac{e^{i\phi}}{\sqrt{2}}|1\rangle
$$

其中 $\phi$ 是相对相位。这一相位在物理上对应 $x$ 轴相对于 $z$ 轴的具体方位约定——选择不同的 $\phi$ 相当于重新定义坐标轴的取向。按照标准约定，取 $\phi = 0$：

$$
|r\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)
$$

由正交归一条件 $\langle r|l\rangle = 0$ 和 $\langle l|l\rangle = 1$，可确定：
$$
|l\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)
$$

（整体相位因子不可观测，因此 $|l\rangle$ 也可乘 $e^{i\chi}$，但不影响后续算符构造。）

### 3.3 矩阵形式的推导

$\hat{\sigma}_x$ 满足：
$$
\hat{\sigma}_x|r\rangle = +|r\rangle, \quad \hat{\sigma}_x|l\rangle = -|l\rangle
$$

设 $\sigma_x = \begin{pmatrix} a & b \\ c & d \end{pmatrix}$，代入 $|r\rangle$ 的本征方程：
$$
\begin{pmatrix} a & b \\ c & d \end{pmatrix}\begin{pmatrix} 1/\sqrt{2} \\ 1/\sqrt{2} \end{pmatrix} = \begin{pmatrix} 1/\sqrt{2} \\ 1/\sqrt{2} \end{pmatrix}
$$

得到：
$$
\frac{a+b}{\sqrt{2}} = \frac{1}{\sqrt{2}} \Rightarrow a+b=1, \quad \frac{c+d}{\sqrt{2}} = \frac{1}{\sqrt{2}} \Rightarrow c+d=1
$$

代入 $|l\rangle$ 的本征方程：
$$
\begin{pmatrix} a & b \\ c & d \end{pmatrix}\begin{pmatrix} 1/\sqrt{2} \\ -1/\sqrt{2} \end{pmatrix} = -\begin{pmatrix} 1/\sqrt{2} \\ -1/\sqrt{2} \end{pmatrix} = \begin{pmatrix} -1/\sqrt{2} \\ 1/\sqrt{2} \end{pmatrix}
$$

得到：
$$
\frac{a-b}{\sqrt{2}} = \frac{-1}{\sqrt{2}} \Rightarrow a-b=-1, \quad \frac{c-d}{\sqrt{2}} = \frac{1}{\sqrt{2}} \Rightarrow c-d=1
$$

联立求解：
- $a+b=1$ 与 $a-b=-1$ 得 $a=0, b=1$
- $c+d=1$ 与 $c-d=1$ 得 $c=1, d=0$

因此：
$$
\sigma_x = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}
$$

---

## 4 构造 $\hat{\sigma}_y$ 与Pauli矩阵完备组

### 4.1 $\hat{\sigma}_y$ 的本征态与矩阵

类似地，$y$ 方向自旋本征态可由实验和相位约定确定为：
$$
|i\rangle = \frac{1}{\sqrt{2}}(|0\rangle + i|1\rangle), \quad |o\rangle = \frac{1}{\sqrt{2}}(|0\rangle - i|1\rangle)
$$

（符号 $i$ 表示"in"，$o$ 表示"out"，分别对应本征值 $+1$ 和 $-1$。）

验证正交归一性：
$$
\langle i|o\rangle = \frac{1}{2}(1\cdot 1 + (-i)(-i)) = \frac{1}{2}(1 - 1) = 0
$$

通过本征方程 $\hat{\sigma}_y|i\rangle = +|i\rangle$ 和 $\hat{\sigma}_y|o\rangle = -|o\rangle$，类似推导可得：

$$
\sigma_y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}
$$

### 4.2 Pauli矩阵的定义

三个自旋分量算符 $\hat{\sigma}_x, \hat{\sigma}_y, \hat{\sigma}_z$ 在 $S_z$ 表象下的矩阵表示合称 **Pauli矩阵**：

> **Pauli矩阵**：
> $$ \sigma_x = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \quad \sigma_y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}, \quad \sigma_z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix} $$

形式上可写成矢量：
$$
\vec{\sigma} = \sigma_x \hat{x} + \sigma_y \hat{y} + \sigma_z \hat{z}
$$

注意区分两种"矢量"概念：$\vec{\sigma}$ 是三维实空间中的矢量算符（其分量是算符），而量子态 $|\psi\rangle$ 是二维复向量空间中的态矢。

---

## 5 任意方向的自旋算符

### 5.1 单位矢量方向的投影

对于任意空间方向 $\hat{n} = (n_x, n_y, n_z)$（满足 $n_x^2 + n_y^2 + n_z^2 = 1$），自旋分量算符为：
$$
\hat{\sigma}_n = \vec{\hat{\sigma}} \cdot \hat{n} = n_x \hat{\sigma}_x + n_y \hat{\sigma}_y + n_z \hat{\sigma}_z
$$

其矩阵表示为：
$$
\sigma_n = n_x \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix} + n_y \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix} + n_z \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix} = \begin{pmatrix} n_z & n_x - in_y \\ n_x + in_y & -n_z \end{pmatrix}
$$

### 5.2 本征值的验证

计算特征方程 $\det(\sigma_n - \lambda I) = 0$：
$$
\det\begin{pmatrix} n_z - \lambda & n_x - in_y \\ n_x + in_y & -n_z - \lambda \end{pmatrix} = (n_z-\lambda)(-n_z-\lambda) - (n_x-in_y)(n_x+in_y)
$$

展开：
$$
= -n_z^2 + \lambda^2 - (n_x^2 + n_y^2) = \lambda^2 - (n_x^2 + n_y^2 + n_z^2) = \lambda^2 - 1 = 0
$$

因此本征值恒为 $\lambda = \pm 1$，与方向无关。这再次确认了自旋 $1/2$ 的量子化特性：无论沿哪个方向测量，结果总是 $\pm 1$。

---
