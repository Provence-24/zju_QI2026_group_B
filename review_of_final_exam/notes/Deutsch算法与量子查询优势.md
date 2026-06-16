
## 1 从经典黑箱到量子查询

### 1.1 问题设定：四种单比特函数

> **定义（Deutsch问题，1985）**：考虑所有从单比特输入到单比特输出的函数 $f: \{0,1\} \to \{0,1\}$。这样的函数仅有四种：
> - $f_1(x) = 0$（常数零函数）
> - $f_2(x) = x$（恒等函数）
> - $f_3(x) = \bar{x} = 1-x$（非函数）
> - $f_4(x) = 1$（常数壹函数）

**分类**：$f_1, f_4$ 为**常数函数（constant）**，满足 $f(0)=f(1)$；$f_2, f_3$ 为**平衡函数（balanced）**，满足 $f(0)\neq f(1)$。

### 1.2 经典查询的极限

假设我们拥有一个**黑箱（black box）**，可以计算 $f(x)$，但无法查看其内部结构。每次查询只能输入一个 $x$ 值，获得一个输出 $f(x)$。

- 一次经典查询：只能获得 $f(0)$ 或 $f(1)$ 中的一个。例如，若查询得 $f(0)=0$，则 $f$ 可能是 $f_1$ 或 $f_2$，无法确定。
- 确定性区分常数与平衡：必须查询两次，分别获得 $f(0)$ 和 $f(1)$。

> **核心问题**：量子力学是否允许我们通过**一次**黑箱调用，确定性地判断 $f$ 是常数函数还是平衡函数？

---

## 2 量子黑箱的幺正嵌入

### 2.1 可逆计算框架

量子演化必须是幺正的、可逆的。为将经典函数 $f$ 嵌入量子电路，我们采用双寄存器构造：

> **定义（量子函数嵌入）**：对输入寄存器 $|x\rangle$ 和输出寄存器 $|y\rangle$，定义幺正算符 $\hat{U}_f$ 满足
> $$\hat{U}_f|x\rangle|y\rangle = |x\rangle|y \oplus f(x)\rangle,$$
> 其中 $\oplus$ 为模 2 加法（异或）。

**验证幺正性**：$\hat{U}_f^2|x\rangle|y\rangle = |x\rangle|y\oplus f(x)\oplus f(x)\rangle = |x\rangle|y\rangle$，故 $\hat{U}_f = \hat{U}_f^{-1} = \hat{U}_f^\dagger$，确为幺正。

### 2.2 四种函数的电路实现

在标准基下，$\hat{U}_f$ 对应 $4\times 4$ 幺正矩阵：
- $f_1=0$：$\hat{U}_{f_1} = \hat{I}_4$（恒等）
- $f_2=x$：$\hat{U}_{f_2} = \text{CNOT}_{12}$（控制位为输入，目标位翻转）
- $f_3=\bar{x}$：$\hat{U}_{f_3} = \text{CNOT}_{12}(\hat{I}\otimes\hat{X})$（先翻转目标位，再CNOT）
- $f_4=1$：$\hat{U}_{f_4} = \hat{I}\otimes\hat{X}$（目标位恒翻转）

---

## 3 直观尝试：并行计算的局限

### 3.1  naive 并行策略

利用 Hadamard 门制备叠加态，试图一次计算所有函数值：

$$|0\rangle|0\rangle \xrightarrow{\hat{H}\otimes\hat{H}} \frac{1}{2}\big(|0\rangle+|1\rangle\big)\big(|0\rangle+|1\rangle\big) \xrightarrow{\hat{U}_f} \frac{1}{\sqrt{2}}\big(|0\rangle|f(0)\rangle + |1\rangle|f(1)\rangle\big).$$

末态同时编码了 $f(0)$ 和 $f(1)$，看似实现了并行计算。

### 3.2 测量困境

为提取信息，对两比特施加 $\hat{H}\otimes\hat{H}$ 后测量。分别计算四种情形：

- **$f_1=0$**：末态 $\frac{1}{\sqrt{2}}|0\rangle(|0\rangle+|1\rangle)$，测量得 $00$ 或 $01$。
- **$f_2=x$**：末态 $\frac{1}{\sqrt{2}}(|00\rangle-|11\rangle)$，测量得 $00$ 或 $11$。
- **$f_3=\bar{x}$**：末态 $\frac{1}{\sqrt{2}}(|00\rangle+|11\rangle)$，测量得 $00$ 或 $11$。
- **$f_4=1$**：末态 $\frac{1}{\sqrt{2}}|0\rangle(|0\rangle-|1\rangle)$，测量得 $00$ 或 $01$。

**分析**：若测得 $01$，可知 $f$ 为常数；若测得 $11$，可知 $f$ 为平衡。但有一半概率测得 $00$，此时完全无法区分。总体成功率仅 $50\%$，与随机猜测无异。

> **结论**：简单的量子并行性不足以实现确定性区分。必须利用**量子干涉**将函数的全局性质编码到可观测的振幅中。

---

## 4 Deutsch算法：一次查询的确定性区分

### 4.1 算法电路

Deutsch算法的核心电路为：

$$
\begin{array}{c}
|1\rangle \longrightarrow \boxed{\hat{H}} \longrightarrow \boxed{\hat{U}_f} \longrightarrow \boxed{\hat{H}} \longrightarrow \text{测量} \\
|1\rangle \longrightarrow \boxed{\hat{H}} \longrightarrow \boxed{\hat{U}_f} \longrightarrow \text{（不操作）}
\end{array}
$$

即两比特均初始化为 $|1\rangle$，先各自通过 $\hat{H}$，再经过 $\hat{U}_f$，最后第一比特再次通过 $\hat{H}$ 并测量。

### 4.2 逐步推导

**步骤一：制备叠加**

$$\hat{H}|1\rangle = \frac{1}{\sqrt{2}}\big(|0\rangle-|1\rangle\big) \equiv |-\rangle.$$

初态经 $\hat{H}\otimes\hat{H}$ 后：

$$|\psi_1\rangle = |-\rangle|-\rangle = \frac{1}{2}\big(|0\rangle-|1\rangle\big)\big(|0\rangle-|1\rangle\big).$$

**步骤二：相位反冲（Phase Kickback）**

计算 $\hat{U}_f$ 对第二比特处于 $|-\rangle$ 态的作用：

$$\hat{U}_f|x\rangle|-\rangle = |x\rangle\frac{1}{\sqrt{2}}\big(|f(x)\rangle-|1\oplus f(x)\rangle\big).$$

若 $f(x)=0$，则 $|0\rangle-|1\rangle = |-\rangle$；若 $f(x)=1$，则 $|1\rangle-|0\rangle = -|-\rangle$。统一写为

$$\hat{U}_f|x\rangle|-\rangle = (-1)^{f(x)}|x\rangle|-\rangle.$$

**关键观察**：函数值通过相位因子 $(-1)^{f(x)}$ 被"反冲"回输入寄存器，输出寄存器保持 $|-\rangle$ 不变。

因此，经过 $\hat{U}_f$ 后：

$$|\psi_2\rangle = \frac{1}{2}\sum_{x=0}^1 (-1)^{f(x)}|x\rangle|-\rangle = \frac{1}{\sqrt{2}}\Big((-1)^{f(0)}|0\rangle+(-1)^{f(1)}|1\rangle\Big)|-\rangle.$$

**步骤三：Hadamard 干涉**

对第一比特施加 $\hat{H}$，利用 $\hat{H}|0\rangle = |+\rangle = \frac{1}{\sqrt{2}}(|0\rangle+|1\rangle)$ 和 $\hat{H}|1\rangle = |-\rangle = \frac{1}{\sqrt{2}}(|0\rangle-|1\rangle)$。

- **若 $f$ 为常数**（$f(0)=f(1)$）：$(-1)^{f(0)} = (-1)^{f(1)} \equiv \lambda$，
  $$|\psi_3\rangle = \lambda \hat{H}\frac{1}{\sqrt{2}}\big(|0\rangle+|1\rangle\big)|-\rangle = \lambda|0\rangle|-\rangle.$$
  测量第一比特，**确定得到 $|0\rangle$**。

- **若 $f$ 为平衡**（$f(0)\neq f(1)$）：$(-1)^{f(1)} = -(-1)^{f(0)}$，
  $$|\psi_3\rangle = (-1)^{f(0)} \hat{H}\frac{1}{\sqrt{2}}\big(|0\rangle-|1\rangle\big)|-\rangle = (-1)^{f(0)}|1\rangle|-\rangle.$$
  测量第一比特，**确定得到 $|1\rangle$**。

### 4.3 物理诠释

Deutsch算法通过三个关键机制实现量子优势：
1. **叠加**：输入寄存器同时查询 $x=0$ 和 $x=1$；
2. **相位反冲**：利用辅助比特的 $|-\rangle$ 态，将函数值转化为输入态的相对相位；
3. **干涉**：末态 Hadamard 门将相位信息转化为可区分的计算基态。

输出寄存器始终处于 $|-\rangle$，不携带可提取信息；函数的全局性质（常数 vs 平衡）被完全编码于输入寄存器的测量结果中。

### 4.4 等效电路视角

利用量子电路恒等式可深入理解算法为何有效：

- $\hat{H}^2 = \hat{I}$；
- $\hat{H}\hat{X}\hat{H} = \hat{Z}$；
- $\hat{H}\otimes\hat{H} \cdot \text{CNOT} \cdot \hat{H}\otimes\hat{H} = \text{CNOT}_{21}$（控制位与目标位互换）。

将四种 $\hat{U}_f$ 用这些恒等式化简后，Deutsch电路分别等效为：
- $f_1=0$：恒等操作；
- $f_2=x$：第一比特受第二比特控制的 $\hat{X}$；
- $f_3=\bar{x}$：第一比特受第二比特控制的 $\hat{X}$ 加 $\hat{Z}$；
- $f_4=1$：对第二比特施加 $\hat{Z}$。

在此视角下，算法的本质是通过 Hadamard 变换将函数查询转化为控制门操作，再经干涉读出控制关系的存在与否。

---
