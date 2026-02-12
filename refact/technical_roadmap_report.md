# Technical Roadmap & Design Report

## 1. Executive Summary
This document outlines the technical roadmap and design progress for the aircraft design project. It includes sizing results, performance analysis, and geometry definition.

## 2. Initial Sizing
The initial sizing is based on the mission requirements.

### 2.1 Weight Estimation
The Maximum Takeoff Weight (MTOW) is estimated using the iterative fuel fraction method.

The core equation for weight buildup is:
$$ W_{TO} = W_{crew} + W_{payload} + W_{fuel} + W_{empty} $$

Using the empty weight fraction regression:
$$ \frac{W_{empty}}{W_{TO}} = A \cdot W_{TO}^{C} \cdot K_{vs} $$

Where:
- $A, C$ are regression constants
- $K_{vs}$ is the variable sweep correction factor

### 2.2 Sizing Results
The convergence history of the sizing loop is shown below.

![Sizing Convergence History](docs/images/sizing_convergence.png)

## 3. Constraint Analysis
The design point (Thrust-to-Weight ratio and Wing Loading) is selected based on performance constraints.

### 3.1 Constraints
The following constraints are considered:
- Takeoff Distance
- Landing Distance
- Cruise Speed
- Climb Gradient
- Turn Performance

The master equation for specific excess power ($P_s$) is:
$$ P_s = V \left( \frac{T}{W} - \frac{C_{D0} q S}{W} - \frac{n^2 k W}{q S} \right) $$

### 3.2 Constraint Diagram
The matching plot showing the feasible design space:

![Constraint Diagram](docs/images/constraint_diagram.png)

## 4. Geometry Definition
The aircraft geometry is defined parametrically and generated using OpenVSP.

### 4.1 3D Model
The generated OpenVSP model views:

![Iso View](docs/images/vsp_iso_view.png)
![Top View](docs/images/vsp_top_view.png)
![Side View](docs/images/vsp_side_view.png)

## 5. Performance Analysis
Detailed performance analysis is conducted for the selected design point.

### 5.1 Drag Polar
The drag polar is estimated as:
$$ C_D = C_{D0} + k C_L^2 $$

Where $k$ is the induced drag factor:
$$ k = \frac{1}{\pi \cdot AR \cdot e} $$

### 5.2 Payload-Range
The payload-range diagram:

![Payload Range Diagram](docs/images/payload_range.png)
