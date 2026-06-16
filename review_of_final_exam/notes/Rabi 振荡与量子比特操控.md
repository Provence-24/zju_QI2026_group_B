

## 1 静磁场的局限与旋转横向磁场的引入

### 1.1 为何静磁场不足以操控量子比特

由笔记一可知，静磁场 $\vec{B} = B\hat{z}$ 仅使 Bloch 矢量绕 $z$ 轴进动，保持极角 $\theta$ 不变。这意味着若系统初始处于 $|0\rangle$（北极），它将永远停留在 $|0\rangle$（至多积累相位），无法被驱动至 $|1\rangle$ 或任意叠加态 $|0\rangle + |1\rangle$。从量子计算的角度，静磁场只能实现 $Z$ 轴方向的相位门，无法完成比特翻转（$X$ 门）或叠加态制备（$H$ 门）。

### 1.2 旋转横向磁场的物理模型

为实现对量子比特的完整操控，需在 $z$ 方向静磁场 $\vec{B}_0 = B_0\hat{z}$ 的基础上，叠加一个在 $xy$ 平面内以角频率 $\omega$ 旋转的横向磁场：

$$\vec{B}_1(t) = B_1(\cos\omega t\,\hat{x} - \sin\omega t\,\hat{y}).$$

总哈密顿量为

$$\hat{H}(t) = -\frac{\hbar\omega_0}{2}\sigma_z - \frac{\hbar\omega_1}{2}\big(\sigma_x\cos\omega t - \sigma_y\sin\omega t\big),$$

其中 $\omega_0 \propto B_0$，$\omega_1 \propto B_1$。第二项显含时间，使薛定谔方程成为耦合微分方程组，直接求解较为复杂。

---

## 2 旋转坐标系中的有效哈密顿量

### 2.1 从实验室系到旋转系的幺正变换

引入一个与横向磁场同步旋转的参考系。定义绕 $z$ 轴转动的幺正算符

$$\hat{R}(t) = \exp\left(i\frac{\omega t}{2}\sigma_z\right).$$

旋转系中的态矢量定义为 $|\psi'(t)\rangle = \hat{R}(t)|\psi(t)\rangle$。我们需要推导 $|\psi'(t)\rangle$ 所满足的薛定谔方程。

对时间求导：

$$i\hbar\frac{\partial|\psi'\rangle}{\partial t} = i\hbar\dot{\hat{R}}|\psi\rangle + \hat{R}\left(i\hbar\frac{\partial|\psi\rangle}{\partial t}\right).$$

利用 $\dot{\hat{R}} = \frac{i\omega}{2}\sigma_z\hat{R}$ 以及原薛定谔方程 $i\hbar\partial_t|\psi\rangle = \hat{H}(t)|\psi\rangle$：

$$i\hbar\frac{\partial|\psi'\rangle}{\partial t} = \left[-\frac{\hbar\omega}{2}\sigma_z + \hat{R}\hat{H}(t)\hat{R}^\dagger\right]|\psi'\rangle.$$

### 2.2 有效哈密顿量的导出

计算相似变换 $\hat{R}\hat{H}(t)\hat{R}^\dagger$。利用恒等式

$$\hat{R}\sigma_z\hat{R}^\dagger = \sigma_z,$$
$$\hat{R}\sigma_x\hat{R}^\dagger = \sigma_x\cos\omega t + \sigma_y\sin\omega t,$$
$$\hat{R}\sigma_y\hat{R}^\dagger = -\sigma_x\sin\omega t + \sigma_y\cos\omega t,$$

可得

$$\hat{R}\big(\sigma_x\cos\omega t - \sigma_y\sin\omega t\big)\hat{R}^\dagger = \sigma_x.$$

因此，旋转系中的有效哈密顿量变为时间无关：

$$\hat{H}' = -\frac{\hbar(\omega_0 - \omega)}{2}\sigma_z - \frac{\hbar\omega_1}{2}\sigma_x.$$

**物理诠释**：在随 $\vec{B}_1(t)$ 一同旋转的坐标系中，横向磁场看似静止（沿 $x$ 轴方向），而纵向有效磁场从 $\omega_0$ 减小为失谐量 $\Delta \equiv \omega_0 - \omega$。当旋转频率 $\omega$ 接近拉莫尔频率 $\omega_0$ 时，有效纵向场趋于零，系统仅感受到横向场 $\omega_1$ 的驱动。

---

## 3 Rabi 振荡的严格推导

### 3.1 等效静磁场图像

$\hat{H}'$ 可重写为

$$\hat{H}' = -\frac{\hbar\Omega}{2}\,\hat{n}\cdot\vec{\sigma},$$

其中等效拉比频率 $\Omega$ 与等效磁场方向 $\hat{n}$ 分别为

$$\Omega = \sqrt{(\omega_0 - \omega)^2 + \omega_1^2}, \quad \hat{n} = \left(\frac{\omega_1}{\Omega},\, 0,\, \frac{\omega_0 - \omega}{\Omega}\right).$$

这正是在旋转系中一个自旋在静磁场 $\propto \Omega\hat{n}$ 中的问题。

### 3.2 时间演化算符的显式形式

利用 Pauli 矩阵的指数恒等式（由 $(\hat{n}\cdot\vec{\sigma})^2 = \hat{I}$ 导出）：

$$\exp\left(i\frac{\theta}{2}\hat{n}\cdot\vec{\sigma}\right) = \hat{I}\cos\frac{\theta}{2} + i(\hat{n}\cdot\vec{\sigma})\sin\frac{\theta}{2},$$

旋转系中的时间演化算符为

$$\hat{U}'(t) = \exp\left(-\frac{i\hat{H}'t}{\hbar}\right) = \hat{I}\cos\frac{\Omega t}{2} + i(\hat{n}\cdot\vec{\sigma})\sin\frac{\Omega t}{2}.$$

### 3.3 初态 $|0\rangle$ 的演化与跃迁概率

设初态 $|\psi(0)\rangle = |0\rangle$（实验室系与旋转系在 $t=0$ 时重合）。在旋转系中：

$$|\psi'(t)\rangle = \hat{U}'(t)|0\rangle = \cos\frac{\Omega t}{2}|0\rangle + i\sin\frac{\Omega t}{2}\,(\hat{n}\cdot\vec{\sigma})|0\rangle.$$

计算 $(\hat{n}\cdot\vec{\sigma})|0\rangle$：

$$(\hat{n}\cdot\vec{\sigma})|0\rangle = n_x\sigma_x|0\rangle + n_y\sigma_y|0\rangle + n_z\sigma_z|0\rangle = n_x|1\rangle + n_z|0\rangle,$$

其中用到 $\sigma_x|0\rangle = |1\rangle$，$\sigma_y|0\rangle = i|1\rangle$（但 $n_y=0$），$\sigma_z|0\rangle = |0\rangle$。于是

$$|\psi'(t)\rangle = \left(\cos\frac{\Omega t}{2} + i n_z\sin\frac{\Omega t}{2}\right)|0\rangle + i n_x\sin\frac{\Omega t}{2}|1\rangle.$$

系统处于 $|1\rangle$ 态的概率幅为 $\langle 1|\psi'(t)\rangle = i n_x\sin(\Omega t/2)$。由于 $\hat{R}(t)$ 仅给 $|1\rangle$ 附加一个纯相位因子 $e^{-i\omega t/2}$，实验室系中的概率与之相同：

> **Rabi 公式**：
> $$P_{0\to 1}(t) \equiv |\langle 1|\psi(t)\rangle|^2 = \left(\frac{\omega_1}{\Omega}\right)^2\sin^2\frac{\Omega t}{2}.$$

### 3.4 共振条件与量子门操控

当驱动频率精确匹配拉莫尔频率，即 $\omega = \omega_0$（**共振条件**）时，失谐量 $\Delta = 0$，故 $\Omega = \omega_1$，$n_x = 1$，$n_z = 0$。Rabi 公式简化为

$$P_{0\to 1}(t) = \sin^2\frac{\omega_1 t}{2}.$$

**物理诠释**：在共振时，量子比特在 $|0\rangle$ 与 $|1\rangle$ 之间以角频率 $\omega_1$ 作周期性振荡。通过精确控制脉冲宽度 $t$，可实现特定的量子门操作：
- **$\pi/2$ 脉冲**（$\omega_1 t = \pi/2$）：$P_{0\to 1} = 1/2$，产生最大叠加态 $\frac{1}{\sqrt{2}}(|0\rangle + i|1\rangle)$；
- **$\pi$ 脉冲**（$\omega_1 t = \pi$）：$P_{0\to 1} = 1$，完成比特翻转（$X$ 门）。

Rabi 振荡是量子计算中操控量子比特的最基本物理过程。

---
