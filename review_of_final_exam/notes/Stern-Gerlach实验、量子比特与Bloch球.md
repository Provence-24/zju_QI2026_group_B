
## 1 Stern-Gerlach实验：自旋的量子化证据

### 1.1 实验装置与经典预期

Stern-Gerlach实验（1922年）让一束银原子通过沿 $z$ 轴方向的非均匀磁场 $\vec{B}(z) = B(z)\hat{z}$，随后落在玻璃探测板上。银原子（电子组态 $[\mathrm{Kr}]4d^{10}5s^1$）具有由未配对 $5s$ 电子自旋 $S=1/2$ 贡献的磁矩。原子在磁场梯度中受到的力为：
$$
F_z \propto \frac{dB}{dz}
$$

**经典预期**：若自旋是经典矢量，其方向在空间中是连续分布的，那么磁矩在 $z$ 轴上的投影也应连续取值。原子束经过磁场后应在探测板上展宽为一条连续带。

**实验结果**：当电磁铁开启时，银原子束分裂为**两条**分立的路径，在探测板上形成两个清晰的斑点。这直接证明了角动量（自旋）在特定方向上的投影是**量子化**的，只能取离散值。

### 1.2 级联实验揭示的自旋本质

进一步的级联实验揭示了更深层的量子特性：

**实验 A**：将第一个 Stern-Gerlach 装置（沿 $z$ 方向）的两束之一挡住，让另一束进入**同方向**的第二个 Stern-Gerlach 装置。结果：光束**不再分裂**。这说明经过第一次筛选后，原子已处于确定的 $z$ 方向自旋本征态，再次测量同一分量不会引入新的不确定性。

**实验 B**：将第二个 Stern-Gerlach 装置旋转，使其磁场沿 $x$ 方向。结果：原本处于 $z$ 方向本征态的单束**再次分裂为两束**，且两束强度相等。

**物理诠释**：如果自旋是经典比特那样的布尔量 $\{0,1\}$，一旦确定了 $z$ 分量，$x$ 分量也应确定，不应再次分裂。实验 B 表明，自旋态不能简单地用经典集合描述。自旋态属于一个**二维复向量空间 $\mathbb{C}^2$**，这正是量子比特的数学载体。

---

## 2 从经典比特到量子比特

### 2.1 经典比特的抽象

经典计算机操作由 $0$ 和 $1$ 组成的串。一个经典比特可由物理系统实现，如电容器的充放电状态，或磁化方向的上下。在数学上，我们可将两个状态表示为二维实空间中的正交单位向量：
$$
|0\rangle \equiv |\uparrow\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}, \quad |1\rangle \equiv |\downarrow\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}
$$

经典系统要么处于 $|0\rangle$，要么处于 $|1\rangle$，不能同时处于两者。

### 2.2 量子比特的叠加

量子力学将这两个状态提升为复向量空间 $\mathbb{C}^2$ 的一组标准正交基。一个**量子比特（qubit）**的一般态为两者的线性叠加：
$$
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle = \begin{pmatrix} \alpha \\ \beta \end{pmatrix}, \quad \alpha, \beta \in \mathbb{C}
$$

归一化条件（概率守恒）要求：
$$
\langle\psi|\psi\rangle = |\alpha|^2 + |\beta|^2 = 1
$$

这意味着量子系统可以处于基态的任意叠加态，这是量子计算与量子信息的核心资源。

---

## 3 Bloch球：量子态的几何表示

### 3.1 参数化与整体相位的消去

由于物理概率仅依赖于振幅的模方，整体相位因子 $e^{i\chi}$ 不产生可观测差异：$|\psi\rangle$ 与 $e^{i\chi}|\psi\rangle$ 代表同一物理态。利用这一自由度，我们可以将两个复参数 $\alpha, \beta$（4个实参数）在归一化约束（1个方程）和整体相位等价（1个自由度）下，约化为**2个独立实参数**。

标准的参数化形式为：

> **Bloch球参数化**：
> $$ |\psi\rangle = \cos\frac{\theta}{2}|0\rangle + e^{i\phi}\sin\frac{\theta}{2}|1\rangle $$
> 其中 $\theta \in [0,\pi]$，$\phi \in [0, 2\pi)$。

### 3.2 为什么使用 $\theta/2$ 而非 $\theta$

若使用 $\theta$ 而非 $\theta/2$，即参数化 $|\psi\rangle = \cos\theta|0\rangle + e^{i\phi}\sin\theta|1\rangle$，则两组不同的参数 $(\theta, \phi)$ 与 $(\pi-\theta, \pi+\phi)$ 会描述同一物理态：

$$
\cos(\pi-\theta)|0\rangle + e^{i(\pi+\phi)}\sin(\pi-\theta)|1\rangle = -\cos\theta|0\rangle - e^{i\phi}\sin\theta|1\rangle = -|\psi\rangle
$$

由于 $-|\psi\rangle$ 与 $|\psi\rangle$ 仅差整体相位 $e^{i\pi} = -1$，物理上不可区分。这意味着球面上两个不同的点对应同一量子态，映射不是**一一映射（one-to-one）**。使用 $\theta/2$ 消除了这一冗余，使得每个量子态（射线）唯一对应Bloch球面上的一个点。

### 3.3 Bloch球的几何结构

Bloch球是半径为1的球面：
- **北极** $(\theta=0)$：$|0\rangle$
- **南极** $(\theta=\pi)$：$|1\rangle$
- **赤道** $(\theta=\pi/2)$：等权重叠加态，如 $\phi=0$ 处的 $|+\rangle = \frac{|0\rangle+|1\rangle}{\sqrt{2}}$，$\phi=\pi/2$ 处的 $\frac{|0\rangle+i|1\rangle}{\sqrt{2}}$ 等

> **重要注记**：Bloch球上的点代表量子态，但球面上的几何距离**不**直接对应量子态的内积。例如 $|0\rangle$ 与 $|1\rangle$ 在Bloch球上位于相反的两极，其欧氏位置矢量反向，但量子力学中它们的内积 $\langle 0|1\rangle = 0$（正交），而球面上两点间的弦距离为2。Bloch球是一种方便的视觉辅助，但不应与希尔伯特空间的度量混淆。

---
