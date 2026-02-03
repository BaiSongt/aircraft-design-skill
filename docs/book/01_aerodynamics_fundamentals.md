# 空气动力学基础理论

## 1. 流体力学基础

### 1.1 连续性方程

对于不可压缩流体，连续性方程为：

$$ \nabla \cdot \mathbf{V} = 0 $$

其中：
- $\mathbf{V}$ 为速度矢量

对于可压缩流体，连续性方程为：

$$ \frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{V}) = 0 $$

其中：
- $\rho$ 为流体密度
- $t$ 为时间

### 1.2 动量方程（欧拉方程）

$$ \frac{\partial \mathbf{V}}{\partial t} + (\mathbf{V} \cdot \nabla) \mathbf{V} = -\frac{1}{\rho} \nabla p + \mathbf{g} $$

其中：
- $p$ 为压力
- $\mathbf{g}$ 为重力加速度矢量

### 1.3 伯努利方程

对于定常、无粘、不可压缩流动，沿流线有：

$$ p + \frac{1}{2}\rho V^2 + \rho gz = \text{constant} $$

其中：
- $V$ 为流速
- $z$ 为高度

## 2. 翼型理论

### 2.1 翼型几何参数

#### 2.1.1 翼弦

翼弦 $c$ 是翼型前缘到后缘的直线距离。

#### 2.1.2 相对厚度

翼型相对厚度 $t/c$ 定义为：

$$ \frac{t}{c} = \frac{h_{\text{max}}}{c} $$

其中：
- $h_{\text{max}}$ 为翼型最大厚度

#### 2.1.3 相对弯度

翼型相对弯度 $f/c$ 定义为：

$$ \frac{f}{c} = \frac{f_{\text{max}}}{c} $$

其中：
- $f_{\text{max}}$ 为中弧线最大弯度

### 2.2 升力系数

#### 2.2.1 升力系数定义

$$ C_L = \frac{L}{\frac{1}{2}\rho V^2 S} $$

其中：
- $L$ 为升力
- $S$ 为参考面积

#### 2.2.2 升力线斜率

对于薄翼型理论，升力线斜率为：

$$ C_{L\alpha} = 2\pi \quad (\text{单位：1/rad}) $$

对于有限展弦比机翼，升力线斜率为：

$$ C_{L\alpha} = \frac{2\pi}{1 + \frac{2}{AR}} $$

其中：
- $AR$ 为展弦比

考虑后掠角的影响：

$$ C_{L\alpha} = \frac{2\pi \cos\Lambda}{1 + \frac{2}{AR\cos\Lambda}} $$

其中：
- $\Lambda$ 为后掠角

### 2.3 阻力系数

#### 2.3.1 阻力系数定义

$$ C_D = \frac{D}{\frac{1}{2}\rho V^2 S} $$

其中：
- $D$ 为阻力

#### 2.3.2 极曲线

阻力极曲线通常表示为：

$$ C_D = C_{D0} + K C_L^2 $$

其中：
- $C_{D0}$ 为零升阻力系数
- $K$ 为诱导阻力因子

#### 2.3.3 诱导阻力因子

$$ K = \frac{1}{\pi e AR} $$

其中：
- $e$ 为奥斯瓦尔德效率因子

### 2.4 力矩系数

#### 2.4.1 俯仰力矩系数

$$ C_m = \frac{M}{\frac{1}{2}\rho V^2 S c} $$

其中：
- $M$ 为俯仰力矩
- $c$ 为平均气动弦长

#### 2.4.2 气动中心

气动中心是力矩系数不随迎角变化的点，满足：

$$ \frac{dC_m}{d\alpha} = 0 $$

## 3. 边界层理论

### 3.1 雷诺数

$$ Re = \frac{\rho V L}{\mu} $$

其中：
- $L$ 为特征长度
- $\mu$ 为动力粘度

### 3.2 边界层厚度

#### 3.2.1 层流边界层

对于平板层流，边界层厚度为：

$$ \delta = \frac{5.0x}{\sqrt{Re_x}} $$

其中：
- $x$ 为从前缘算起的距离
- $Re_x$ 为局部雷诺数

#### 3.2.2 湍流边界层

对于平板湍流，边界层厚度为：

$$ \delta = \frac{0.37x}{Re_x^{1/5}} $$

### 3.3 摩擦阻力系数

#### 3.3.1 层流摩擦系数

$$ C_f = \frac{1.328}{\sqrt{Re}} $$

#### 3.3.2 湍流摩擦系数

$$ C_f = \frac{0.074}{Re^{0.2}} $$

## 4. 可压缩流动

### 4.1 马赫数

$$ M = \frac{V}{a} $$

其中：
- $a$ 为声速

### 4.2 声速

对于理想气体：

$$ a = \sqrt{\gamma R T} $$

其中：
- $\gamma$ 为比热比（空气 $\gamma = 1.4$）
- $R$ 为气体常数（空气 $R = 287$ J/(kg·K)）
- $T$ 为温度（K）

### 4.3 压缩性修正

#### 4.3.1 普朗特-格劳厄特法则

$$ C_{p,\text{compressible}} = \frac{C_{p,\text{incompressible}}}{\sqrt{1 - M^2}} $$

其中：
- $C_p$ 为压力系数

#### 4.3.2 升力线斜率修正

$$ C_{L\alpha,\text{compressible}} = \frac{C_{L\alpha,\text{incompressible}}}{\sqrt{1 - M^2}} $$

## 5. 后掠翼理论

### 5.1 后掠效应

后掠翼的有效马赫数为：

$$ M_{\text{eff}} = M \cos\Lambda $$

其中：
- $\Lambda$ 为后掠角

### 5.2 后掠翼升力线斜率

$$ C_{L\alpha} = \frac{2\pi \cos\Lambda}{1 + \frac{2}{AR\cos\Lambda}} $$

## 6. 三维效应

### 6.1 展弦比

$$ AR = \frac{b^2}{S} $$

其中：
- $b$ 为翼展
- $S$ 为机翼面积

### 6.2 梢根比

$$ \lambda = \frac{c_t}{c_r} $$

其中：
- $c_t$ 为翼梢弦长
- $c_r$ 为翼根弦长

### 6.3 平均气动弦长

$$ \bar{c} = \frac{2}{3} c_r \frac{1 + \lambda + \lambda^2}{1 + \lambda} $$

## 7. 高升力装置

### 7.1 襟翼类型

#### 7.1.1 简单襟翼

襟翼偏转产生的升力系数增量：

$$ \Delta C_{L,\text{flap}} = \frac{S_{\text{flap}}}{S} \Delta C_{L,\text{2D}} \cos^2\Lambda_{\text{hinge}} $$

其中：
- $S_{\text{flap}}$ 为襟翼面积
- $\Lambda_{\text{hinge}}$ 为襟翼铰链线后掠角

#### 7.1.2 缝翼

缝翼通过延迟边界层分离来增加升力系数。

### 7.2 最大升力系数

#### 7.2.1 干净构型

$$ C_{L,\text{max,clean}} = C_{L,\alpha} \alpha_{\text{stall}} $$

其中：
- $\alpha_{\text{stall}}$ 为失速迎角

#### 7.2.2 襟翼构型

$$ C_{L,\text{max,flap}} = C_{L,\text{max,clean}} + \Delta C_{L,\text{flap}} $$

## 8. 失速特性

### 8.1 失速速度

$$ V_{\text{stall}} = \sqrt{\frac{2W}{\rho S C_{L,\text{max}}}} $$

其中：
- $W$ 为飞机重量

### 8.2 失速迎角

对于对称翼型，失速迎角通常为：

$$ \alpha_{\text{stall}} \approx 15^\circ \sim 18^\circ $$

## 9. 下洗效应

### 9.1 下洗角

$$ \epsilon = \frac{C_L}{\pi AR} $$

### 9.2 有效迎角

$$ \alpha_{\text{eff}} = \alpha - \epsilon $$

## 10. 动压

$$ q = \frac{1}{2}\rho V^2 $$

## 11. 压力系数

$$ C_p = \frac{p - p_\infty}{\frac{1}{2}\rho V_\infty^2} $$

其中：
- $p$ 为局部压力
- $p_\infty$ 为自由流压力
- $V_\infty$ 为自由流速度

## 12. 库塔-儒可夫斯基变换

库塔-儒可夫斯基变换将圆柱绕流转换为翼型绕流：

$$ z = \zeta + \frac{a^2}{\zeta} $$

其中：
- $z$ 为物理平面
- $\zeta$ 为辅助平面
- $a$ 为圆柱半径

## 13. 库塔条件

库塔条件要求翼型后缘处速度有限：

$$ V_{\text{TE}} = \text{finite} $$

这决定了环量 $\Gamma$ 的值。

## 14. 环量与升力关系

根据库塔-儒可夫斯基定理：

$$ L = \rho V_\infty \Gamma $$

其中：
- $\Gamma$ 为环量

## 15. 压力中心

压心位置为：

$$ x_{\text{cp}} = x_{\text{ac}} - \frac{C_{m0}}{C_L} \bar{c} $$

其中：
- $x_{\text{ac}}$ 为气动中心位置
- $C_{m0}$ 为零升力矩系数

## 16. 马赫锥

对于超声速流动，扰动传播范围受马赫锥限制：

$$ \mu = \arcsin\left(\frac{1}{M}\right) $$

其中：
- $\mu$ 为马赫角

## 17. 激波

### 17.1 正激波

正激波前后参数关系：

$$ \frac{p_2}{p_1} = 1 + \frac{2\gamma}{\gamma + 1}(M_1^2 - 1) $$

$$ \frac{T_2}{T_1} = \frac{[2\gamma M_1^2 - (\gamma - 1)][(\gamma - 1)M_1^2 + 2]}{(\gamma + 1)^2 M_1^2} $$

$$ \frac{\rho_2}{\rho_1} = \frac{(\gamma + 1)M_1^2}{2 + (\gamma - 1)M_1^2} $$

### 17.2 斜激波

斜激波角 $\beta$ 与偏转角 $\theta$ 的关系：

$$ \tan\theta = 2\cot\beta \frac{M_1^2\sin^2\beta - 1}{M_1^2(\gamma + \cos 2\beta) + 2} $$

## 18. 膨胀波

普朗特-迈耶膨胀波关系：

$$ \nu(M) = \sqrt{\frac{\gamma + 1}{\gamma - 1}} \arctan\sqrt{\frac{\gamma - 1}{\gamma + 1}(M^2 - 1)} - \arctan\sqrt{M^2 - 1} $$

其中：
- $\nu(M)$ 为普朗特-迈耶函数

## 19. 面积律

跨声速面积律要求：

$$ \frac{dS}{dx} = \text{constant} $$

其中：
- $S$ 为飞机横截面积
- $x$ 为纵向位置

## 20. 波阻

$$ C_{D,\text{wave}} = \frac{4\pi^2}{S} \frac{A'^2}{l^2} $$

其中：
- $A'$ 为等效体积分布的导数
- $l$ 为飞机长度

## 参考文献

1. Anderson, J. D. *Fundamentals of Aerodynamics*, McGraw-Hill
2. Abbott, I. H., von Doenhoff, A. E. *Theory of Wing Sections*, Dover
3. Kuethe, A. M., Chow, C.-Y. *Foundations of Aerodynamics*, Wiley
4. Bertin, J. J., Cummings, R. M. *Critical Hypothetical Aerodynamics*, AIAA
