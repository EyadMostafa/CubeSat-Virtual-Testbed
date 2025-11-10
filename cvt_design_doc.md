# **CVT Design Document**

Document Version: 1.6 (Live)  
Last Updated: 2025-11-09

## **1\. Project Vision & Core Goal**

The primary goal is to create a high-fidelity, real-time **virtual testbed** (a "digital twin") for a cubic satellite.

This is **not** just a 3D visualization. It is a full-physics simulation designed to be a research tool. The primary research objective is to **investigate various TinyML methodologies (e.g., quantization, pruning, novel architectures) to determine which techniques achieve the highest accuracy-to-performance ratio within the severe constraints of a CubeSat platform.**

This testbed will serve as a "digital leaderboard" to run a "bake-off" between different TinyML approaches. It will provide *quantitative* data on how each methodology's unique resource profile (power draw, CPU time) causes cascading impacts on the satellite's overall mission performance (e.g., pointing accuracy, data throughput, and battery health over a 24-hour simulation).

## **2\. Guiding Principles**

* **The Server is the Truth:** The Python backend is the *single source of truth* for all simulation state (position, attitude, power, etc.). The frontend is a "dumb" renderer.  
* **State-Based Communication:** The server broadcasts the *complete state* at each tick, not a list of *actions*. This ensures the client is always in sync with the truth, even if packets are lost.  
* **Iterative Realism:** We will build the simulation layer by layer (Crawl, Walk, Run). Each new layer of physics (e.g., atmospheric drag) adds to a stable, working core.  
* **Model, Don't Mimic:** The simulation is only useful if it can *fail* realistically. We will model the *constraints* (e.g., a "dead" battery) and their consequences (e.g., the ADCS shutting down).

## **3\. System Architecture**

The system is a **decoupled client-server architecture** designed to be a modular and extensible "plug-and-play" framework.

### **3.1. Backend: Python "Simulation Kernel" (cvt/backend/)**

* **Role:** The "Simulation." This is the single source of truth.  
* **Framework:** **FastAPI**. This is the core web framework that serves all API endpoints and handles WebSocket connections.  
* **Logic:** A central SimulationKernel class runs the main "tick" loop. On each tick, it calls various "plugged-in" subsystem modules (e.g., OrbitalPropagator, AttitudeDynamics) to calculate the new satellite state. The kernel is also responsible for calculating the Earth's correct rotational angle (earth\_rotation\_angle) based on the simulated time and time\_warp\_factor, providing this to the frontend.

### **3.2. Frontend: Three.js "Renderer" (cvt/frontend/)**

* **Role:** The "Visualizer." Renders the 3D scene and provides the User Interface (UI).  
* **Framework:** **three.js** for 3D rendering and **Tailwind CSS** for the UI, all running in a modern JavaScript module (main.js).  
* **Logic:** The frontend is a "dumb" client. It opens a WebSocket connection and does *nothing* but listen. On every message, it updates the 3D models and UI elements to match the new state received from the server.  
* **Smoothing:** The frontend is responsible for *smoothing* the low-frequency (e.g., 10Hz) data stream for a high-frequency (e.g., 60Hz) display. It uses **Linear Interpolation (lerp)** for position and **Spherical Linear Interpolation (slerp)** for rotation to prevent "jitter" and provide a smooth, continuous visualization.

#### **3.2.1. Frontend Visualization Strategy**

To be useful, the frontend must be *informationally* accurate, not *physically* accurate. A 1:1 scale is impossible (e.g., an Earth the size of a basketball would make the CubeSat an invisible speck of dust).

* **Artistic Scale:** We adopt an "artistic" scale. By default, the Earth is rendered with a radius of 6 units, and a scale factor of 1/1000 is used to convert the backend's kilometer-based positions. This maps a \~6,771km LEO orbit to a \~6.77 unit orbit, making it visually distinct but close to the Earth model.  
* **Exaggeration:** The CubeSat model itself is *dramatically* exaggerated in size (e.g., 0.2 units) so it is clearly visible to the user.  
* **Interpolation (Anti-Jitter):** The backend "Physics Clock" (e.g., 10Hz) is much slower than the frontend "Render Clock" (e.g., 60Hz). To prevent the satellite and Earth from "teleporting" on each tick, the frontend must interpolate:  
  * **lerp(target, 0.1):** The satellite's position (a Vector3) is smoothed using lerp. On each frame, it moves 10% of the remaining distance to its target position.  
  * **slerp(target, 0.1):** The Earth's rotation (a Quaternion) is smoothed using slerp. This correctly handles angular interpolation (e.g., the 359° to 1° problem) and provides a smooth spin.

### **3.3. Interface: WebSocket**

* **Protocol:** A persistent WebSocket connection (at /ws) is the "data firehose."  
* **Data:** The SimulationKernel broadcasts the complete SatelliteState (a Pydantic model serialized to JSON) to all connected clients on every tick.

### **3.4. Multi-Client Broadcast (One-to-Many)**

The ConnectionManager is designed as a **broadcaster**. This means the simulation kernel doesn't just talk to one client; it broadcasts its state to *all* connected clients. This allows for:

* **Multiple Viewers:** The entire research team can connect and watch the *same* simulation in real-time.  
* **Headless Data Loggers:** A simple Python script can connect to the *same* stream to log all telemetry to a .csv file for later analysis.  
* **2D Dashboards:** A separate web page (e.g., using Plotly or Grafana) can connect to the *same* stream to render real-time graphs of power, attitude error, etc.

## **4\. Development Roadmap (Crawl, Walk, Run)**

This is the iterative plan for building the testbed.

### **Phase 1: Crawl (The "Point Mass") \- COMPLETE**

* **Goal:** Simulate **position** and **Earth rotation** in a time-warped, real-time environment.  
* **Status:** The backend is fully built, configured, and running. The SimulationKernel calculates the orbit (using poliastro) and Earth's rotation, and broadcasts the SatelliteState over a FastAPI WebSocket. The frontend three.js scene can connect, lerp/slerp the data, and display a smooth, jitter-free visualization.

### **Phase 2: Walk (The "Tumbling Body")**

* **Goal:** Simulate **attitude** (orientation). Make the CubeSat a full 3D object that can be pointed.  
* **Backend Tasks:**  
  1. Implement the AttitudeDynamics module.  
  2. Solve **Euler's equations of motion** (scipy.integrate.solve\_ivp).  
  3. Implement a basic ADCSModule with a **PID controller**.  
  4. Update the SimulationKernel to call these modules and populate the SatelliteState.attitude fields.  
* **Frontend Tasks:**  
  1. Parse the attitude quaternion from the SatelliteState.  
  2. Use cube.quaternion.slerp() to smoothly interpolate the *CubeSat's* rotation.  
  3. Implement the WebGLRenderTarget to show the "live camera feed" from the CubeSat's perspective.

### **Phase 3: Run (The "Realistic Spacecraft")**

* **Goal:** Simulate the **space environment**. The ADCS must now fight against real-world forces.  
* **Backend Tasks:**  
  1. Implement the EnvironmentModule with fidelity flags.  
  2. Add **Atmospheric Drag** (using pyNRLMSISE-00 and config.spacecraft).  
  3. Add **Gravity Gradient Torque**.  
  4. Add **Solar Radiation Pressure (SRP) Torque.**  
  5. Add **Magnetic Torque** (using wmm-calculator).  
  6. Feed all of these as "disturbance torques" into the AttitudeDynamics module.

### **Phase 4: Beyond (The "TinyML Bake-Off")**

* **Goal:** Run the core research experiment: **compare competing TinyML methodologies** in a fully constrained environment.  
* **Backend Tasks:**  
  1. Implement the ConstraintsModule (PowerSystem and OnboardComputer).  
  2. **Emulate Power:** Model the battery, solar panel generation, and component power draw (based on *real hardware benchmarks*).  
  3. **Emulate Compute:** Emulate the *time delay* (ms) and *CPU load* (%) of the AI payload.  
  4. **Emulate Camera:** Implement the CameraEmulator to degrade "perfect" GEE images with noise, blur, and compression.  
  5. **Run the Bake-Off:**  
     * Run a 24-hour simulation with model A (e.g., an int8 quantized model).  
     * Run the *same* 24-hour simulation with model B (e.g., a "pruned" float16 model).  
     * Log the results (accuracy, power failures, pointing error) from both to find the superior *mission-level* methodology.

### **Phase 5: The Ultimate Goal (Hardware-in-the-Loop)**

* **Goal:** Provide the final validation for the *winning* TinyML methodology on the *actual* flight hardware.  
* **Tasks:** Create a new HIL\_Interface module that "unplugs" the *emulated* OnboardComputer.  
  1. The CVT (on the PC) will simulate the physics and generate *fake sensor signals*.  
  2. These signals will be sent over a physical wire (e.g., USB-to-I2C) to the *real, physical* flight hardware.  
  3. The *real* hardware will run its *real* flight code (with the chosen TinyML model), thinking it's in space.  
  4. The CVT will "catch" the *real* actuator commands (e.g., a PWM signal) from the hardware.  
  5. This *real* command will be fed *back into* the simulation, closing the loop.

## **5\. Error Handling Methodology**

The simulation will adhere to a strict, 3-policy system for robustness.

1. **Policy 1: Strict on Startup (Fail Fast & Loud)**  
   * **Applies to:** Configuration & Initialization Errors (e.g., bad config.yaml, missing TLE).  
   * **Action:** The code will logger.critical() the error and **raise SystemExit(1)** to force a hard crash. The server *must not* start in an invalid state.  
2. **Policy 2: Resilient in Runtime (Fail Gracefully)**  
   * **Applies to:** Unexpected *Physics* or *Code* Errors during a \_tick (e.g., a scipy solver fails).  
   * **Action:** The \_simulation\_loop will catch Exception, logger.error(), and **push a CRITICAL alert** to the SatelliteState. The loop will then *continue*. The server *must not* crash for all users because of one bad tick.  
3. **Policy 3: Simulate the Consequence (This is Not an Error)**  
   * **Applies to:** Emulated "failures" that are the *goal* of the simulation (e.g., battery at 0%, CPU at 100%).  
   * **Action:** This is a **state**, not an exception. The PowerSystem will *not* raise an error. It will set state.hardware.power.charge\_level \= 0\. The ADCS module *must* then read this state and command zero torque. The simulation proves the consequence of a dead battery.

## **6\. Operational Modes**

The simulation is designed to test three primary data-gathering modes.

1. **Strip Mapping (Automatic):** The default "lawnmower" mode. The simulation's auto\_capture\_interval\_sec setting will automatically add a "take picture" task to the queue at a regular interval.  
2. **Spot Tasking (Manual):** Simulates a ground-station command. We will have a POST /api/command/take\_picture endpoint that allows a user (or another script) to manually add a "take picture" task to the queue.  
3. **"Tip and Cue" (AI-Driven):** The advanced, autonomous mode. The *AI model itself*, after running on a "strip" image, will have the ability to identify a target and *autonomously* add a new, high-priority "spot task" to the queue.