# 🛰️ **CubeSat Virtual Testbed (CVT)**

A **high-fidelity, real-time "digital twin"** of a CubeSat, designed as a **testbed** for AI payloads and GNC (Guidance, Navigation, and Control) algorithms.

This project serves as the **primary development and validation tool** for the AI payload on our research team's real-world CubeSat.  
Its purpose is to provide a _"sim-to-real"_ environment that is as **rough** (physics) and **constrained** (hardware) as space itself — enabling testing and validation of AI methodologies under realistic mission conditions.

---

## 🚀 **About the Project**

This is **not just a 3D visualization** — it’s a **full-stack, "source-of-truth" simulation** that models the entire spacecraft as a coupled system.

The core goal is to run a **"bake-off"** between different TinyML methodologies (e.g., _quantization_ vs. _pruning_) to evaluate how their unique performance profiles (power draw, CPU time) impact the satellite’s **mission performance** (e.g., pointing accuracy, battery life) over a simulated **24-hour orbital run**.
For more details checkout the **cvt_design_doc.md**

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
