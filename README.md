# 🛰️ CubeSat Virtual Testbed (CVT)
*A lightweight, ML-centric digital twin for CubeSat onboard AI research.*

CVT is a **real-time virtual testbed** designed to evaluate TinyML models under the same **power, compute, timing, and imaging constraints** experienced by CubeSats in orbit.  
Instead of modeling high-fidelity spacecraft physics, CVT focuses on the constraints that actually determine TinyML performance in space:

- Battery charge/discharge behavior  
- Sunlight vs. eclipse cycles  
- Model latency and energy usage  
- Compute bottlenecks and scheduling delays  
- Degraded space-like imagery  
- Mission throughput and missed image opportunities  

The purpose of CVT is to provide a **realistic and repeatable environment** to answer key research questions:

> **How do different TinyML models behave when deployed on a constrained on-orbit platform?**  
> **Which compression or optimization techniques yield the best accuracy-per-compute-per-joule?**  
> **How do compute delays and energy usage translate into mission-level impacts such as missed captures, reduced throughput, and power blackouts?**

This makes CVT a practical, research-driven environment for comparing TinyML methods (quantization, pruning, distillation, efficient architectures) in a controlled, repeatable 24-hour orbital simulation.

---

## 🏁 **Getting Started**

Follow these steps to get the full simulation running on your local machine.

---

### ⚙️ **Prerequisites**

- **Git**
- **Python 3.10.19**  
  (Strict requirement — `poliastro` and its dependencies are pinned to this Python generation.  
  Other versions have not been tested.)
- **Node.js & npm** (for running the frontend development server)
- **pyenv** (highly recommended for managing Python versions)

---

## 🧩 **1. Backend Setup (Python Server)**

### Step 1 — Clone the repository

```bash
git clone https://github.com/EyadMostafa/CubeSat-Virtual-Testbed.git
cd CubeSat-Virtual-Testbed/
```

### Step 2 — Set the correct Python version

```
pyenv install 3.10.19
pyenv local 3.10.19
```

### Step 3 — Create and activate a virtual environment

```
python -m venv .venv
source .venv/bin/activate
```

### Step 4 — Install dependencies in "editable" mode

```
pip install -e .
```

### Step 5 — Run the server

```
uvicorn cvt.backend.run_server:app --reload
```

You should see logs similar to:

```
INFO:     Uvicorn running...
INFO:     SimulationKernel initialized...
```

## 🌐 **2. Frontend Setup (Three.js + Vite)**

### Step 1 — Open a new terminal and navigate to the frontend directory

```
cd CubeSat-Virtual-Testbed/cvt/frontend
```

### Step 2 — Install frontend dependencies

```
npm install
```

### Step 3 — Run the frontend development server

```
npm run dev
```

Once running, open the provided local URL (e.g., http://localhost:5173) in your browser.
You should see the 3D Earth and CubeSat visualization updating in real time as the backend simulation runs.

> ⚙️ **Note:**  
> The simulation runs in **time-warped mode** by default to allow quick validation that it’s functioning correctly.  
> To run the simulation in **real-time orbital speed**, open your `config.yaml` file and set:
>
> ```yaml
> time_warp_factor: 1.0
> ```
>
> (The default value `500.0` accelerates the simulation 500× for faster testing.)
