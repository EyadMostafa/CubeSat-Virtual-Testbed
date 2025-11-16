# **CVT – Lightweight ML-First Design Document (Integrated Full Version)**

**Version:** 1.0 (Integrated Edition)

A complete, ML-centric virtual testbed design for evaluating TinyML techniques under realistic orbital resource constraints — without unnecessary spacecraft physics.

---

# **1. Project Purpose**

The CVT is a **lightweight digital twin** designed to evaluate TinyML models in a realistic orbital context. The goal is to answer the key research question:

> **Which TinyML approach (quantization, pruning, distillation, lightweight architectures) provides the best accuracy–per–compute–per–joule on a CubeSat-class platform?**

To achieve this, the simulator models the constraints that *matter for ML research*: compute, power, timing, and image quality. It intentionally avoids complex spacecraft physics that have no impact on TinyML outcomes.

This system enables:
- Testing multiple TinyML models with real latency and energy profiles
- Modeling battery behavior and solar illumination cycles
- Simulating capture schedules
- Measuring mission-level effects: missed captures, blackouts, throughput

This is **not** a full aerospace simulation — it is an **ML systems research environment**.

---

# **2. Guiding Principles**

1. **Minimal Physics**  
   Only orbit and illumination are modeled. No torques, ADCS physics, or environmental disturbances.

2. **ML-Centric Architecture**  
   Every subsystem exists to support TinyML experimentation, not spacecraft engineering.

3. **Backend as the Source of Truth**  
   Full simulation state lives on the backend; the frontend is a visualizer.

4. **Deterministic 24-hour Experiments**  
   Each model undergoes a repeatable orbital simulation for head-to-head comparison.

---

# **3. System Architecture**

## **3.1 Backend — Python Simulation Kernel**

The backend maintains all state and simulates resource constraints affecting ML performance.

### **Core Modules**

---

### **1. OrbitModule**
- Two-body orbit propagation (via poliastro)
- Earth rotation angle
- Coordinate transformation (ECI → lat/lon)
- Sunlight/eclipse determination

**Purpose:** Provide orbital context for power generation and image opportunities.

---

### **2. AttitudeModule (Simplified)**
- No Euler equations
- No rigid-body attitude dynamics
- Supports simple pointing commands:
  - `point_to(lat, lon)`
  - optional `slew_rate_limit`

**Purpose:** Determine whether the satellite can image a ground point — without full ADCS simulation.

---

### **3. TaskScheduler**
Handles:
- **Strip Mapping** (automatic periodic imaging)
- **Spot Tasking** (manual or AI-triggered tasks)

Each task specifies:
- target coordinates
- time
- priority
- pointing requirement

---

### **4. CameraModule**
Loads and degrades representative images:
- Gaussian noise
- Blur
- Compression artifacts

**Purpose:** Deliver realistic inputs for ML inference.

---

### **5. PowerSystem**
Models:
- Battery state of charge (SOC)
- Solar panel generation (sunlit vs eclipse)
- Power consumption:
  - baseline loads
  - camera capture cost
  - ML inference cost (model-dependent)

Equation:
```
SOC[t+1] = SOC[t] + (P_solar - P_load) * Δt
```

**Purpose:** Simulate mission-critical power constraints that affect ML throughput.

---

### **6. ComputeEmulator**
Profiles each model for:
- Inference latency
- Energy usage per inference
- CPU/MCU utilization
- Accuracy

Simulation effects:
- Task delays due to inference
- Energy reduction per inference
- Missed capture opportunities
- Model comparison via mission-level metrics

---

### **7. Logger**
Logs at each tick:
- Battery power data
- ML inference attempts & results
- Camera captures
- Missed tasks
- Accuracy
- Throughput
- Blackouts
- End-of-mission summary

---

## **3.2 Frontend — Three.js Renderer**

A visual layer that:
- Renders Earth at artistic scale
- Renders CubeSat position & simplified orientation
- Displays telemetry:
  - battery percentage
  - sunlight/eclipse state
  - current task
  - last inference result
  - footprint projection

Uses **lerp/slerp** for smoothing. Contains no physics.

---

## **3.3 WebSocket Interface**

Server → Client telemetry:
- Position
- Orientation
- Battery
- Sunlight/eclipse
- Active/scheduled tasks
- Inference metadata

The backend also logs all data for offline analysis.

---

# **4. Development Roadmap**

## **Phase 1 — Minimal Simulation (Completed or Near)**
- Orbit propagation
- Earth rotation
- State broadcast via WebSocket
- Basic Three.js visualization

**Outcome:** Smooth orbital visualization.

---

## **Phase 2 — ML Experimentation Core**
Build the core research tools:
- PowerSystem
- Simplified AttitudeModule
- ComputeEmulator
- CameraModule
- TaskScheduler
- Logging

**Outcome:** Capable of running 24h TinyML experiments.

---

## **Phase 3 — TinyML Bake-Off Experiments**
Test multiple models:
- int8 quantized
- FP16
- pruned
- distilled
- efficient architectures (MobileNet/EfficientNet-Lite)

For each model:
- Run a 24h simulation
- Log mission-level metrics
- Compare accuracy-per-joule, throughput, reliability

**Outcome:** A full ML systems research study.

---

## **Phase 4 — Optional Extensions**
- Improved camera degradation
- Compression pipeline
- Simple thermal throttling
- Smarter scheduling heuristics

Aerospace complexity is not added unless required.

---

# **5. Error Handling**

### **Startup (Strict)**
Invalid config → crash immediately.

### **Runtime (Resilient)**
Physics or compute errors set an error flag but do not crash the system.

### **Simulated Failures (Expected)**
Battery at 0% disables camera & inference. This is a *state*, not an exception.

---

# **6. Key Outputs**

## **Model-Level Metrics**
- Accuracy
- Latency
- Energy per inference
- Throughput

## **Mission-Level Metrics**
- Images captured
- Images processed
- Missed captures
- Power blackouts
- CPU load
- Overall mission yield per joule

---



