# 飞机动力学建模理论

## 1. 建模基础

### 1.1 建模假设

飞机动力学建模通常基于以下假设：

1. **刚性飞机假设**：飞机为刚体，不考虑弹性变形
2. **小扰动假设**：扰动量足够小，可以线性化
3. **质量恒定假设**：飞行过程中质量不变
4. **对称平面假设**：飞机关于 $xz$ 平面对称
5. **地球平坦假设**：忽略地球曲率
6. **标准大气假设**：使用标准大气模型

### 1.2 坐标系定义

#### 1.2.1 惯性坐标系 $O_I x_I y_I z_I$

- 原点 $O_I$：地面上某固定点
- $x_I$ 轴：指向北
- $y_I$ 轴：指向东
- $z_I$ 轴：指向下

#### 1.2.2 机体坐标系 $O_b x_b y_b z_b$

- 原点 $O_b$：飞机质心
- $x_b$ 轴：沿机身纵轴，指向前方
- $y_b$ 轴：沿机翼展向，指向右侧
- $z_b$ 轴：垂直于 $x_b y_b$ 平面，指向下方

#### 1.2.3 稳定坐标系 $O_s x_s y_s z_s$

- 原点 $O_s$：飞机质心
- $x_s$ 轴：沿速度矢量方向
- $z_s$ 轴：在飞机对称面内，垂直于 $x_s$ 轴
- $y_s$ 轴：垂直于 $x_s z_s$ 平面

#### 1.2.4 风轴坐标系 $O_w x_w y_w z_w$

- 原点 $O_w$：飞机质心
- $x_w$ 轴：沿相对风速方向
- $z_w$ 轴：在飞机对称面内，垂直于 $x_w$ 轴
- $y_w$ 轴：垂直于 $x_w z_w$ 平面

### 1.3 欧拉角转换

从惯性坐标系到机体坐标系的转换：

$$ \begin{bmatrix} x_b \\ y_b \\ z_b \end{bmatrix} = \mathbf{R}_{I\to b} \begin{bmatrix} x_I \\ y_I \\ z_I \end{bmatrix} $$

转换矩阵：

$$ \mathbf{R}_{I\to b} = \begin{bmatrix} \cos\theta\cos\psi & \cos\theta\sin\psi & -\sin\theta \\ \sin\phi\sin\theta\cos\psi - \cos\phi\sin\psi & \sin\phi\sin\theta\sin\psi + \cos\phi\cos\psi & \sin\phi\cos\theta \\ \cos\phi\sin\theta\cos\psi + \sin\phi\sin\psi & \cos\phi\sin\theta\sin\psi - \sin\phi\cos\psi & \cos\phi\cos\theta \end{bmatrix} $$

其中欧拉角 $(\phi, \theta, \psi)$ 定义为：
- $\phi$：滚转角（绕 $x_b$ 轴）
- $\theta$：俯仰角（绕 $y_b$ 轴）
- $\psi$：偏航角（绕 $z_b$ 轴）

## 2. 运动学方程

### 2.1 速度关系

机体坐标系中的速度与惯性坐标系中的速度关系：

$$ \mathbf{V}_b = \mathbf{R}_{I\to b} \mathbf{V}_I $$

### 2.2 角速度关系

机体坐标系中的角速度与欧拉角变化率关系：

$$ \begin{bmatrix} p \\ q \\ r \end{bmatrix} = \begin{bmatrix} 1 & 0 & -\sin\theta \\ 0 & \cos\phi & \cos\theta\sin\phi \\ 0 & -\sin\phi & \cos\theta\cos\phi \end{bmatrix} \begin{bmatrix} \dot{\phi} \\ \dot{\theta} \\ \dot{\psi} \end{bmatrix} $$

其中：
- $p, q, r$ 分别为绕 $x_b, y_b, z_b$ 轴的角速度分量

### 2.3 欧拉角变化率

$$ \begin{bmatrix} \dot{\phi} \\ \dot{\theta} \\ \dot{\psi} \end{bmatrix} = \begin{bmatrix} 1 & \sin\phi\tan\theta & \cos\phi\tan\theta \\ 0 & \cos\phi & -\sin\phi \\ 0 & \frac{\sin\phi}{\cos\theta} & \frac{\cos\phi}{\cos\theta} \end{bmatrix} \begin{bmatrix} p \\ q \\ r \end{bmatrix} $$

## 3. 动力学方程

### 3.1 力方程

$$ m \frac{d\mathbf{V}_b}{dt} + \boldsymbol{\omega} \times (m\mathbf{V}_b) = \mathbf{F}_b $$

其中：
- $m$ 为飞机质量
- $\mathbf{V}_b = [u, v, w]^T$ 为机体坐标系中的速度矢量
- $\boldsymbol{\omega} = [p, q, r]^T$ 为机体坐标系中的角速度矢量
- $\mathbf{F}_b = [X, Y, Z]^T$ 为机体坐标系中的外力矢量

展开形式：

$$ \begin{bmatrix} \dot{u} \\ \dot{v} \\ \dot{w} \end{bmatrix} = \begin{bmatrix} rv - qw \\ pw - ru \\ qu - pv \end{bmatrix} + \frac{1}{m} \begin{bmatrix} X \\ Y \\ Z \end{bmatrix} $$

### 3.2 力矩方程

$$ \mathbf{I} \frac{d\boldsymbol{\omega}}{dt} + \boldsymbol{\omega} \times (\mathbf{I} \boldsymbol{\omega}) = \mathbf{M}_b $$

其中：
- $\mathbf{I}$ 为惯性张量
- $\mathbf{M}_b = [L, M, N]^T$ 为机体坐标系中的外力矩矢量

展开形式：

$$ \begin{bmatrix} \dot{p} \\ \dot{q} \\ \dot{r} \end{bmatrix} = \mathbf{I}^{-1} \left( \begin{bmatrix} L \\ M \\ N \end{bmatrix} - \begin{bmatrix} p \\ q \\ r \end{bmatrix} \times (\mathbf{I} \begin{bmatrix} p \\ q \\ r \end{bmatrix}) \right) $$

### 3.3 导航方程

$$ \begin{bmatrix} \dot{x}_I \\ \dot{y}_I \\ \dot{z}_I \end{bmatrix} = \mathbf{R}_{b\to I} \begin{bmatrix} u \\ v \\ w \end{bmatrix} $$

## 4. 气动力和力矩模型

### 4.1 气动力系数

$$ \begin{bmatrix} C_X \\ C_Y \\ C_Z \end{bmatrix} = \frac{1}{\bar{q}S} \begin{bmatrix} X \\ Y \\ Z \end{bmatrix} $$

其中：
- $\bar{q} = \frac{1}{2}\rho V^2$ 为动压
- $S$ 为参考面积

### 4.2 气动力矩系数

$$ \begin{bmatrix} C_l \\ C_m \\ C_n \end{bmatrix} = \frac{1}{\bar{q}S\bar{c}} \begin{bmatrix} L \\ M \\ N \end{bmatrix} $$

其中：
- $\bar{c}$ 为平均气动弦长

### 4.3 稳定坐标系中的气动力

$$ \begin{bmatrix} C_D \\ C_Y \\ C_L \end{bmatrix} = \mathbf{T}_{b\to s} \begin{bmatrix} C_X \\ C_Y \\ C_Z \end{bmatrix} $$

转换矩阵：

$$ \mathbf{T}_{b\to s} = \begin{bmatrix} \cos\alpha\cos\beta & \sin\beta & \sin\alpha\cos\beta \\ -\cos\alpha\sin\beta & \cos\beta & -\sin\alpha\sin\beta \\ -\sin\alpha & 0 & \cos\alpha \end{bmatrix} $$

其中：
- $\alpha$ 为迎角
- $\beta$ 为侧滑角

### 4.4 极曲线模型

$$ C_D = C_{D0} + K C_L^2 $$

其中：
- $C_{D0}$ 为零升阻力系数
- $K = \frac{1}{\pi e AR}$ 为诱导阻力因子
- $e$ 为奥斯瓦尔德效率因子

### 4.5 升力系数模型

$$ C_L = C_{L0} + C_{L\alpha}\alpha $$

其中：
- $C_{L0}$ 为零迎角升力系数
- $C_{L\alpha}$ 为升力线斜率

## 5. 小扰动线性化

### 5.1 扰动变量定义

$$ u = u_0 + \Delta u $$
$$ v = v_0 + \Delta v $$
$$ w = w_0 + \Delta w $$
$$ p = p_0 + \Delta p $$
$$ q = q_0 + \Delta q $$
$$ r = r_0 + \Delta r $$
$$ \theta = \theta_0 + \Delta \theta $$
$$ \phi = \phi_0 + \Delta \phi $$
$$ \psi = \psi_0 + \Delta \psi $$

### 5.2 纵向小扰动方程

$$ \begin{bmatrix} \Delta\dot{u} \\ \Delta\dot{w} \\ \Delta\dot{q} \\ \Delta\dot{\theta} \end{bmatrix} = \mathbf{A}_{\text{long}} \begin{bmatrix} \Delta u \\ \Delta w \\ \Delta q \\ \Delta \theta \end{bmatrix} + \mathbf{B}_{\text{long}} \Delta\delta_e $$

其中：

$$ \mathbf{A}_{\text{long}} = \begin{bmatrix} X_u & X_w & 0 & -g\cos\theta_0 \\ Z_u & Z_w & u_0 + Z_q & -g\sin\theta_0 \\ M_u & M_w & M_q & 0 \\ 0 & 0 & 1 & 0 \end{bmatrix} $$

$$ \mathbf{B}_{\text{long}} = \begin{bmatrix} X_{\delta_e} \\ Z_{\delta_e} \\ M_{\delta_e} \\ 0 \end{bmatrix} $$

动力系数：

$$ X_u = \frac{\partial X}{\partial u} = -\bar{q}S \left( \frac{\partial C_D}{\partial M} \frac{1}{a} + \frac{2C_D}{V} \right) $$

$$ Z_u = \frac{\partial Z}{\partial u} = \bar{q}S \left( \frac{\partial C_L}{\partial M} \frac{1}{a} + \frac{2C_L}{V} \right) $$

$$ M_u = \frac{\partial M}{\partial u} = \bar{q}S\bar{c} \left( \frac{\partial C_m}{\partial M} \frac{1}{a} + \frac{2C_m}{V} \right) $$

### 5.3 横航向小扰动方程

$$ \begin{bmatrix} \Delta\dot{v} \\ \Delta\dot{p} \\ \Delta\dot{r} \\ \Delta\dot{\phi} \\ \Delta\dot{\psi} \end{bmatrix} = \mathbf{A}_{\text{lat}} \begin{bmatrix} \Delta v \\ \Delta p \\ \Delta r \\ \Delta \phi \\ \Delta \psi \end{bmatrix} + \mathbf{B}_{\text{lat}} \begin{bmatrix} \Delta\delta_a \\ \Delta\delta_r \end{bmatrix} $$

其中：

$$ \mathbf{A}_{\text{lat}} = \begin{bmatrix} Y_v & 0 & Y_r & g\cos\theta_0 & -u_0\cos\theta_0 \\ L_v & L_p & L_r & 0 & 0 \\ N_v & N_p & N_r & 0 & 0 \\ 0 & 1 & \tan\theta_0 & 0 & 0 \\ 0 & 0 & \sec\theta_0 & 0 & 0 \end{bmatrix} $$

$$ \mathbf{B}_{\text{lat}} = \begin{bmatrix} Y_{\delta_a} & Y_{\delta_r} \\ L_{\delta_a} & L_{\delta_r} \\ N_{\delta_a} & N_{\delta_r} \\ 0 & 0 \\ 0 & 0 \end{bmatrix} $$

动力系数：

$$ Y_v = \frac{\partial Y}{\partial v} = \bar{q}S \frac{\partial C_Y}{\partial \beta} $$

$$ L_v = \frac{\partial L}{\partial v} = \bar{q}Sb \frac{\partial C_l}{\partial \beta} $$

$$ N_v = \frac{\partial N}{\partial v} = \bar{q}Sb \frac{\partial C_n}{\partial \beta} $$

## 6. 模态分析

### 6.1 特征方程

$$ |\mathbf{A} - \lambda\mathbf{I}| = 0 $$

### 6.2 纵向模态

#### 6.2.1 短周期模态

特征方程：

$$ \lambda^2 + 2\zeta_{\text{sp}}\omega_{n,\text{sp}}\lambda + \omega_{n,\text{sp}}^2 = 0 $$

固有频率：

$$ \omega_{n,\text{sp}} = \sqrt{-M_w Z_u - Z_q M_u} $$

阻尼比：

$$ \zeta_{\text{sp}} = \frac{M_u + Z_q}{2\sqrt{-M_w Z_u - Z_q M_u}} $$

#### 6.2.2 长周期模态

特征方程：

$$ \lambda^2 + 2\zeta_{\text{ph}}\omega_{n,\text{ph}}\lambda + \omega_{n,\text{ph}}^2 = 0 $$

固有频率：

$$ \omega_{n,\text{ph}} = \sqrt{-\frac{g Z_u}{u_0}} $$

阻尼比：

$$ \zeta_{\text{ph}} = \frac{X_u - \frac{Z_u}{u_0}M_w}{2\sqrt{-\frac{g Z_u}{u_0}}} $$

### 6.3 横航向模态

#### 6.3.1 滚转收敛模态

特征方程：

$$ \lambda - L_p = 0 $$

特征值：

$$ \lambda = L_p $$

时间常数：

$$ \tau_{\text{roll}} = -\frac{1}{L_p} $$

#### 6.3.2 螺旋模态

特征方程：

$$ \lambda^2 + (L_p - N_r)\lambda + (N_p L_r - N_v L_p) = 0 $$

#### 6.3.3 荷兰滚模态

特征方程：

$$ \lambda^2 + 2\zeta_{\text{dr}}\omega_{n,\text{dr}}\lambda + \omega_{n,\text{dr}}^2 = 0 $$

固有频率：

$$ \omega_{n,\text{dr}} = \sqrt{N_v Y_v - Y_r N_v} $$

阻尼比：

$$ \zeta_{\text{dr}} = \frac{N_p + Y_r}{2\sqrt{N_v Y_v - Y_r N_v}} $$

## 7. 状态空间表示

### 7.1 纵向状态空间

$$ \dot{\mathbf{x}}_{\text{long}} = \mathbf{A}_{\text{long}}\mathbf{x}_{\text{long}} + \mathbf{B}_{\text{long}}\mathbf{u}_{\text{long}} $$

$$ \mathbf{y}_{\text{long}} = \mathbf{C}_{\text{long}}\mathbf{x}_{\text{long}} + \mathbf{D}_{\text{long}}\mathbf{u}_{\text{long}} $$

其中：

$$ \mathbf{x}_{\text{long}} = \begin{bmatrix} \Delta u \\ \Delta w \\ \Delta q \\ \Delta \theta \end{bmatrix} $$

$$ \mathbf{u}_{\text{long}} = \begin{bmatrix} \Delta\delta_e \end{bmatrix} $$

### 7.2 横航向状态空间

$$ \dot{\mathbf{x}}_{\text{lat}} = \mathbf{A}_{\text{lat}}\mathbf{x}_{\text{lat}} + \mathbf{B}_{\text{lat}}\mathbf{u}_{\text{lat}} $$

$$ \mathbf{y}_{\text{lat}} = \mathbf{C}_{\text{lat}}\mathbf{x}_{\text{lat}} + \mathbf{D}_{\text{lat}}\mathbf{u}_{\text{lat}} $$

其中：

$$ \mathbf{x}_{\text{lat}} = \begin{bmatrix} \Delta v \\ \Delta p \\ \Delta r \\ \Delta \phi \\ \Delta \psi \end{bmatrix} $$

$$ \mathbf{u}_{\text{lat}} = \begin{bmatrix} \Delta\delta_a \\ \Delta\delta_r \end{bmatrix} $$

## 8. 传递函数

### 8.1 纵向传递函数

#### 8.1.1 升降舵到俯仰角速度

$$ \frac{q(s)}{\delta_e(s)} = \frac{K_q (s + z)}{s^2 + 2\zeta_{\text{sp}}\omega_{n,\text{sp}}s + \omega_{n,\text{sp}}^2} $$

#### 8.1.2 升降舵到迎角

$$ \frac{\alpha(s)}{\delta_e(s)} = \frac{K_\alpha (s + z_\alpha)}{s^2 + 2\zeta_{\text{sp}}\omega_{n,\text{sp}}s + \omega_{n,\text{sp}}^2} $$

### 8.2 横航向传递函数

#### 8.2.1 副翼到滚转角速度

$$ \frac{p(s)}{\delta_a(s)} = \frac{K_p}{s - L_p} $$

#### 8.2.2 方向舵到偏航角速度

$$ \frac{r(s)}{\delta_r(s)} = \frac{K_r (s + z_r)}{s^2 + 2\zeta_{\text{dr}}\omega_{n,\text{dr}}s + \omega_{n,\text{dr}}^2} $$

## 9. 频率响应

### 9.1 幅频特性

$$ |G(j\omega)| = \frac{|N(j\omega)|}{|D(j\omega)|} $$

### 9.2 相频特性

$$ \angle G(j\omega) = \angle N(j\omega) - \angle D(j\omega) $$

### 9.3 伯德图

伯德图由幅频特性和相频特性组成：
- 幅频特性：$20\log_{10}|G(j\omega)|$ vs $\log_{10}\omega$
- 相频特性：$\angle G(j\omega)$ (度) vs $\log_{10}\omega$

## 10. 根轨迹分析

### 10.1 根轨迹定义

根轨迹是系统特征根随参数变化的轨迹。

### 10.2 根轨迹性质

1. 根轨迹对称于实轴
2. 根轨迹起始于开环极点，终止于开环零点或无穷远
3. 根轨迹在实轴上的段数为奇数

### 10.3 根轨迹绘制规则

1. 确定开环极点和零点
2. 确定实轴上的根轨迹段
3. 确定渐近线
4. 确定分离点和会合点
5. 确定出射角和入射角

## 11. 仿真方法

### 11.1 数值积分方法

#### 11.1.1 欧拉法

$$ \mathbf{x}_{k+1} = \mathbf{x}_k + h f(\mathbf{x}_k, t_k) $$

#### 11.1.2 龙格-库塔法

$$ \mathbf{x}_{k+1} = \mathbf{x}_k + \frac{h}{6}(k_1 + 2k_2 + 2k_3 + k_4) $$

其中：

$$ k_1 = f(\mathbf{x}_k, t_k) $$
$$ k_2 = f(\mathbf{x}_k + \frac{h}{2}k_1, t_k + \frac{h}{2}) $$
$$ k_3 = f(\mathbf{x}_k + \frac{h}{2}k_2, t_k + \frac{h}{2}) $$
$$ k_4 = f(\mathbf{x}_k + hk_3, t_k + h) $$

### 11.2 仿真步骤

1. 初始化状态变量
2. 计算气动力和力矩
3. 计算状态导数
4. 数值积分更新状态
5. 重复步骤2-4

## 12. 参数辨识

### 12.1 最小二乘法

$$ \boldsymbol{\theta} = (\mathbf{X}^T\mathbf{X})^{-1}\mathbf{X}^T\mathbf{y} $$

其中：
- $\boldsymbol{\theta}$ 为待辨识参数
- $\mathbf{X}$ 为回归矩阵
- $\mathbf{y}$ 为观测数据

### 12.2 递推最小二乘法

$$ \boldsymbol{\theta}_{k+1} = \boldsymbol{\theta}_k + \mathbf{K}_k(\mathbf{y}_k - \mathbf{x}_k^T\boldsymbol{\theta}_k) $$

其中：

$$ \mathbf{K}_k = \frac{\mathbf{P}_k\mathbf{x}_k}{1 + \mathbf{x}_k^T\mathbf{P}_k\mathbf{x}_k} $$
$$ \mathbf{P}_{k+1} = (\mathbf{I} - \mathbf{K}_k\mathbf{x}_k^T)\mathbf{P}_k $$

## 13. 鲁棒性分析

### 13.1 不确定性建模

$$ \dot{\mathbf{x}} = (\mathbf{A} + \Delta\mathbf{A})\mathbf{x} + (\mathbf{B} + \Delta\mathbf{B})\mathbf{u} $$

### 13.2 鲁棒稳定性

系统鲁棒稳定条件：

$$ \text{Re}[\lambda_i(\mathbf{A} + \Delta\mathbf{A})] < 0, \quad \forall i, \forall \Delta\mathbf{A} $$

### 13.3 H∞范数

$$ ||\mathbf{G}(s)||_\infty = \sup_{\omega} \bar{\sigma}[\mathbf{G}(j\omega)] $$

其中：
- $\bar{\sigma}[\cdot]$ 为最大奇异值

## 14. 控制系统设计

### 14.1 PID控制

$$ u(t) = K_p e(t) + K_i \int_0^t e(\tau)d\tau + K_d \frac{de(t)}{dt} $$

### 14.2 状态反馈控制

$$ \mathbf{u} = -\mathbf{K}\mathbf{x} $$

其中：
- $\mathbf{K}$ 为反馈增益矩阵

### 14.3 LQR控制

$$ J = \int_0^\infty (\mathbf{x}^T\mathbf{Q}\mathbf{x} + \mathbf{u}^T\mathbf{R}\mathbf{u})dt $$

最优控制：

$$ \mathbf{u}^* = -\mathbf{R}^{-1}\mathbf{B}^T\mathbf{P}\mathbf{x} $$

其中 $\mathbf{P}$ 为黎卡提方程的解：

$$ \mathbf{A}^T\mathbf{P} + \mathbf{P}\mathbf{A} - \mathbf{P}\mathbf{B}\mathbf{R}^{-1}\mathbf{B}^T\mathbf{P} + \mathbf{Q} = 0 $$

## 参考文献

1. Stevens, B. L., Lewis, F. L. *Aircraft Control and Simulation*, Wiley
2. Roskam, J. *Airplane Flight Dynamics and Automatic Flight Controls*, DARcorporation
3. Phillips, W. F. *Mechanics of Flight*, Wiley
4. Zipfel, P. H. *Modeling and Simulation of Aerospace Vehicle Dynamics*, AIAA
5. Blakelock, J. H. *Automatic Control of Aircraft and Missiles*, Wiley
