# 飞机动力学与稳定性理论

## 1. 坐标系

### 1.1 机体坐标系

机体坐标系 $O_b x_b y_b z_b$ 定义为：
- 原点 $O_b$：飞机质心
- $x_b$ 轴：沿机身纵轴，指向前方
- $y_b$ 轴：沿机翼展向，指向右侧
- $z_b$ 轴：垂直于 $x_b y_b$ 平面，指向下方

### 1.2 稳定坐标系

稳定坐标系 $O_s x_s y_s z_s$ 定义为：
- 原点 $O_s$：飞机质心
- $x_s$ 轴：沿速度矢量方向
- $z_s$ 轴：在飞机对称面内，垂直于 $x_s$ 轴
- $y_s$ 轴：垂直于 $x_s z_s$ 平面

### 1.3 坐标系转换

从稳定坐标系到机体坐标系的转换矩阵：

$$ \begin{bmatrix} x_b \\ y_b \\ z_b \end{bmatrix} = \begin{bmatrix} \cos\alpha & 0 & \sin\alpha \\ 0 & 1 & 0 \\ -\sin\alpha & 0 & \cos\alpha \end{bmatrix} \begin{bmatrix} x_s \\ y_s \\ z_s \end{bmatrix} $$

其中：
- $\alpha$ 为迎角

## 2. 运动方程

### 2.1 力方程

$$ m \frac{d\mathbf{V}}{dt} = \mathbf{F} $$

其中：
- $m$ 为飞机质量
- $\mathbf{V}$ 为速度矢量
- $\mathbf{F}$ 为外力合力

### 2.2 力矩方程

$$ \mathbf{I} \frac{d\boldsymbol{\omega}}{dt} + \boldsymbol{\omega} \times (\mathbf{I} \boldsymbol{\omega}) = \mathbf{M} $$

其中：
- $\mathbf{I}$ 为惯性张量
- $\boldsymbol{\omega}$ 为角速度矢量
- $\mathbf{M}$ 为外力矩合力矩

### 2.3 欧拉角

欧拉角 $(\phi, \theta, \psi)$ 定义为：
- $\phi$：滚转角（绕 $x_b$ 轴）
- $\theta$：俯仰角（绕 $y_b$ 轴）
- $\psi$：偏航角（绕 $z_b$ 轴）

## 3. 纵向运动方程

### 3.1 纵向小扰动方程

$$ \begin{bmatrix} \dot{u} \\ \dot{w} \\ \dot{q} \\ \dot{\theta} \end{bmatrix} = \mathbf{A}_{\text{long}} \begin{bmatrix} u \\ w \\ q \\ \theta \end{bmatrix} + \mathbf{B}_{\text{long}} \delta_e $$

其中：
- $u$ 为 $x_b$ 方向速度扰动
- $w$ 为 $z_b$ 方向速度扰动
- $q$ 为俯仰角速度扰动
- $\theta$ 为俯仰角扰动
- $\delta_e$ 为升降舵偏转角

### 3.2 纵向动力系数

$$ \mathbf{A}_{\text{long}} = \begin{bmatrix} X_u & X_w & 0 & -g \cos\theta_0 \\ Z_u & Z_w & u_0 + Z_q & -g \sin\theta_0 \\ M_u & M_w & M_q & 0 \\ 0 & 0 & 1 & 0 \end{bmatrix} $$

其中：
- $X_u = \frac{\partial X}{\partial u}$ 为阻力对 $u$ 的导数
- $Z_w = \frac{\partial Z}{\partial w}$ 为升力对 $w$ 的导数
- $M_q = \frac{\partial M}{\partial q}$ 为俯仰阻尼导数
- $M_u = \frac{\partial M}{\partial u}$ 为俯仰力矩对 $u$ 的导数
- $M_w = \frac{\partial M}{\partial w}$ 为俯仰力矩对 $w$ 的导数

## 4. 横航向运动方程

### 4.1 横航向小扰动方程

$$ \begin{bmatrix} \dot{v} \\ \dot{p} \\ \dot{r} \\ \dot{\phi} \\ \dot{\psi} \end{bmatrix} = \mathbf{A}_{\text{lat}} \begin{bmatrix} v \\ p \\ r \\ \phi \\ \psi \end{bmatrix} + \mathbf{B}_{\text{lat}} \begin{bmatrix} \delta_a \\ \delta_r \end{bmatrix} $$

其中：
- $v$ 为 $y_b$ 方向速度扰动
- $p$ 为滚转角速度扰动
- $r$ 为偏航角速度扰动
- $\phi$ 为滚转角扰动
- $\psi$ 为偏航角扰动
- $\delta_a$ 为副翼偏转角
- $\delta_r$ 为方向舵偏转角

### 4.2 横航向动力系数

$$ \mathbf{A}_{\text{lat}} = \begin{bmatrix} Y_v & 0 & Y_r & g \cos\theta_0 & -u_0 \cos\theta_0 \\ L_v & L_p & L_r & 0 & 0 \\ N_v & N_p & N_r & 0 & 0 \\ 0 & 1 & \tan\theta_0 & 0 & 0 \\ 0 & 0 & \sec\theta_0 & 0 & 0 \end{bmatrix} $$

其中：
- $Y_v = \frac{\partial Y}{\partial v}$ 为侧力对 $v$ 的导数
- $L_p = \frac{\partial L}{\partial p}$ 为滚转阻尼导数
- $L_r = \frac{\partial L}{\partial r}$ 为滚转力矩对 $r$ 的导数
- $N_p = \frac{\partial N}{\partial p}$ 为偏航力矩对 $p$ 的导数
- $N_r = \frac{\partial N}{\partial r}$ 为偏航阻尼导数

## 5. 静稳定性

### 5.1 纵向静稳定性

#### 5.1.1 纵向静稳定性判据

$$ C_{m\alpha} < 0 $$

其中：
- $C_{m\alpha} = \frac{\partial C_m}{\partial \alpha}$ 为俯仰力矩系数对迎角的导数

#### 5.1.2 静稳定裕度

$$ SM = \frac{x_{\text{np}} - x_{\text{cg}}}{\bar{c}} $$

其中：
- $x_{\text{np}}$ 为中性点位置
- $x_{\text{cg}}$ 为重心位置
- $\bar{c}$ 为平均气动弦长

#### 5.1.3 中性点

$$ x_{\text{np}} = \frac{C_{L\alpha,\text{wing}} x_{\text{ac,wing}} + C_{L\alpha,\text{ht}} x_{\text{ac,ht}}}{C_{L\alpha,\text{wing}} + C_{L\alpha,\text{ht}}} $$

其中：
- $C_{L\alpha,\text{wing}}$ 为机翼升力线斜率
- $C_{L\alpha,\text{ht}}$ 为平尾升力线斜率
- $x_{\text{ac,wing}}$ 为机翼气动中心位置
- $x_{\text{ac,ht}}$ 为平尾气动中心位置

### 5.2 航向静稳定性

#### 5.2.1 航向静稳定性判据

$$ C_{n\beta} > 0 $$

其中：
- $C_{n\beta} = \frac{\partial C_n}{\partial \beta}$ 为偏航力矩系数对侧滑角的导数

### 5.3 横向静稳定性

#### 5.3.1 横向静稳定性判据

$$ C_{l\beta} < 0 $$

其中：
- $C_{l\beta} = \frac{\partial C_l}{\partial \beta}$ 为滚转力矩系数对侧滑角的导数

## 6. 动稳定性

### 6.1 特征方程

$$ |\mathbf{A} - \lambda \mathbf{I}| = 0 $$

其中：
- $\mathbf{A}$ 为动力系数矩阵
- $\lambda$ 为特征值
- $\mathbf{I}$ 为单位矩阵

### 6.2 纵向模态

#### 6.2.1 短周期模态

短周期模态特征方程：

$$ \lambda^2 + 2\zeta_{\text{sp}} \omega_{n,\text{sp}} \lambda + \omega_{n,\text{sp}}^2 = 0 $$

其中：
- $\zeta_{\text{sp}}$ 为短周期阻尼比
- $\omega_{n,\text{sp}}$ 为短周期固有频率

#### 6.2.2 长周期模态

长周期模态特征方程：

$$ \lambda^2 + 2\zeta_{\text{ph}} \omega_{n,\text{ph}} \lambda + \omega_{n,\text{ph}}^2 = 0 $$

其中：
- $\zeta_{\text{ph}}$ 为长周期阻尼比
- $\omega_{n,\text{ph}}$ 为长周期固有频率

### 6.3 横航向模态

#### 6.3.1 滚转收敛模态

滚转收敛模态特征方程：

$$ \lambda - L_p = 0 $$

#### 6.3.2 螺旋模态

螺旋模态特征方程：

$$ \lambda^2 + (L_p - N_r)\lambda + (N_p L_r - N_v L_p) = 0 $$

#### 6.3.3 荷兰滚模态

荷兰滚模态特征方程：

$$ \lambda^2 + 2\zeta_{\text{dr}} \omega_{n,\text{dr}} \lambda + \omega_{n,\text{dr}}^2 = 0 $$

其中：
- $\zeta_{\text{dr}}$ 为荷兰滚阻尼比
- $\omega_{n,\text{dr}}$ 为荷兰滚固有频率

## 7. 操纵性

### 7.1 操纵面效率

#### 7.1.1 升降舵效率

$$ \frac{\partial C_L}{\partial \delta_e} = \frac{S_{\text{ht}}}{S} \frac{\partial C_{L,\text{ht}}}{\partial \delta_e} $$

其中：
- $S_{\text{ht}}$ 为平尾面积
- $\delta_e$ 为升降舵偏转角

#### 7.1.2 副翼效率

$$ \frac{\partial C_l}{\partial \delta_a} = \frac{S_{\text{aileron}}}{S} \frac{\partial C_{l,\text{aileron}}}{\partial \delta_a} $$

其中：
- $S_{\text{aileron}}$ 为副翼面积
- $\delta_a$ 为副翼偏转角

### 7.2 配平

#### 7.2.1 纵向配平

纵向配平条件：

$$ C_{m0} + C_{m\alpha} \alpha + C_{m\delta_e} \delta_e = 0 $$

其中：
- $C_{m0}$ 为零升力矩系数
- $C_{m\delta_e} = \frac{\partial C_m}{\partial \delta_e}$ 为俯仰力矩系数对升降舵偏转角的导数

#### 7.2.2 横航向配平

横航向配平条件：

$$ C_{l0} + C_{l\beta} \beta + C_{l\delta_a} \delta_a + C_{l\delta_r} \delta_r = 0 $$
$$ C_{n0} + C_{n\beta} \beta + C_{n\delta_a} \delta_a + C_{n\delta_r} \delta_r = 0 $$

其中：
- $C_{l0}$ 为零侧滑角滚转力矩系数
- $C_{n0}$ 为零侧滑角偏航力矩系数
- $C_{l\delta_a} = \frac{\partial C_l}{\partial \delta_a}$ 为滚转力矩系数对副翼偏转角的导数
- $C_{l\delta_r} = \frac{\partial C_l}{\partial \delta_r}$ 为滚转力矩系数对方向舵偏转角的导数
- $C_{n\delta_a} = \frac{\partial C_n}{\partial \delta_a}$ 为偏航力矩系数对副翼偏转角的导数
- $C_{n\delta_r} = \frac{\partial C_n}{\partial \delta_r}$ 为偏航力矩系数对方向舵偏转角的导数

## 8. 惯性特性

### 8.1 惯性矩

#### 8.1.1 绕 $x$ 轴惯性矩

$$ I_x = \int (y^2 + z^2) dm $$

#### 8.1.2 绕 $y$ 轴惯性矩

$$ I_y = \int (x^2 + z^2) dm $$

#### 8.1.3 绕 $z$ 轴惯性矩

$$ I_z = \int (x^2 + y^2) dm $$

### 8.2 惯性积

#### 8.2.1 $I_{xz}$ 惯性积

$$ I_{xz} = \int xz dm $$

#### 8.2.2 $I_{xy}$ 惯性积

$$ I_{xy} = \int xy dm $$

#### 8.2.3 $I_{yz}$ 惯性积

$$ I_{yz} = \int yz dm $$

## 9. 飞行品质

### 9.1 短周期模态飞行品质

#### 9.1.1 阻尼比要求

对于军用飞机，短周期阻尼比要求：

$$ 0.35 \leq \zeta_{\text{sp}} \leq 1.30 $$

#### 9.1.2 固有频率要求

短周期固有频率要求：

$$ \omega_{n,\text{sp}} \geq 1.0 \text{ rad/s} $$

### 9.2 荷兰滚模态飞行品质

#### 9.2.1 阻尼比要求

对于军用飞机，荷兰滚阻尼比要求：

$$ \zeta_{\text{dr}} \geq 0.08 $$

#### 9.2.2 固有频率要求

荷兰滚固有频率要求：

$$ \omega_{n,\text{dr}} \geq 1.0 \text{ rad/s} $$

### 9.3 滚转模态飞行品质

#### 9.3.1 滚转时间常数

滚转时间常数要求：

$$ \tau_{\text{roll}} \leq 1.0 \text{ s} $$

其中：
- $\tau_{\text{roll}} = -\frac{1}{L_p}$ 为滚转时间常数

## 10. 响应特性

### 10.1 阶跃响应

对于二阶系统，阶跃响应为：

$$ y(t) = 1 - \frac{e^{-\zeta \omega_n t}}{\sqrt{1-\zeta^2}} \sin(\omega_d t + \phi) $$

其中：
- $\omega_d = \omega_n \sqrt{1-\zeta^2}$ 为阻尼固有频率
- $\phi = \arccos \zeta$ 为相位角

### 10.2 频率响应

对于二阶系统，幅频特性为：

$$ |G(j\omega)| = \frac{1}{\sqrt{(1 - (\omega/\omega_n)^2)^2 + (2\zeta \omega/\omega_n)^2}} $$

相频特性为：

$$ \angle G(j\omega) = -\arctan\left(\frac{2\zeta \omega/\omega_n}{1 - (\omega/\omega_n)^2}\right) $$

## 11. 过载

### 11.1 过载系数

$$ n = \frac{L}{W} $$

其中：
- $L$ 为升力
- $W$ 为飞机重量

### 11.2 协调转弯

协调转弯条件：

$$ \tan\phi = n \sin\gamma $$

其中：
- $\phi$ 为滚转角
- $\gamma$ 为航迹角

### 11.3 转弯半径

$$ R = \frac{V^2}{g \sqrt{n^2 - \cos^2\gamma}} $$

## 12. 爬升性能

### 12.1 爬升率

$$ RC = V \sin\gamma $$

其中：
- $V$ 为飞行速度
- $\gamma$ 为爬升角

### 12.2 爬升梯度

$$ \sin\gamma = \frac{T - D}{W} $$

其中：
- $T$ 为推力
- $D$ 为阻力

## 13. 下降性能

### 13.1 下降率

$$ RD = -V \sin\gamma $$

### 13.2 下降梯度

$$ \sin\gamma = \frac{T - D}{W} $$

## 14. 机动性能

### 14.1 最大持续过载

$$ n_{\text{max,sustained}} = \frac{T_{\text{max}}}{W} \left(\frac{L}{D}\right)_{\text{max}} $$

其中：
- $T_{\text{max}}$ 为最大可用推力
- $(L/D)_{\text{max}}$ 为最大升阻比

### 14.2 最大瞬时过载

$$ n_{\text{max,instantaneous}} = \frac{C_{L,\text{max}} q S}{W} $$

其中：
- $C_{L,\text{max}}$ 为最大升力系数
- $q = \frac{1}{2}\rho V^2$ 为动压

## 参考文献

1. Roskam, J. *Airplane Flight Dynamics and Automatic Flight Controls*, DARcorporation
2. Etkin, B., Reid, L. D. *Dynamics of Flight: Stability and Control*, Wiley
3. Phillips, W. F. *Mechanics of Flight*, Wiley
4. Cook, M. V. *Flight Dynamics Principles*, Elsevier
5. Zipfel, P. H. *Modeling and Simulation of Aerospace Vehicle Dynamics*, AIAA
