from __future__ import annotations

import asyncio
from logging import getLogger
from datetime import datetime, timezone
from astropy.time import Time
import astropy.units as u

from cvt.config.config import config
from cvt.backend.kernel.state_schema import SatelliteState, Alert
from cvt.backend.kernel.websocket_server import connection_manager
from cvt.backend.subsystems.orbital_propagator import OrbitalPropagator
# from cvt.backend.subsystems.attitude_dynamics import AttitudeDynamics
# from cvt.backend.subsystems.power_system import PowerSystem

logger = getLogger(__name__)

class SimulationKernel:
    """
    Runs the main asynchronous "tick" loop that drives the entire simulation,
    updates the global state, and broadcasts it.
    """
    def __init__(self):
        self.state: SatelliteState = SatelliteState()
        self.tick_duration: float = 1.0 / config.simulation.tick_rate_hz
        self.time_warp_factor: float = config.simulation.time_warp_factor
        self.running: bool = False
        self._simulation_task: asyncio.Task | None = None

        self.propagator: OrbitalPropagator = OrbitalPropagator()
        self.current_sim_time: Time = Time.now()
        
        logger.info(f"SimulationKernel initialized. Tick duration: {self.tick_duration:.2f}s")
        logger.info(f"Time Warp Factor: {self.time_warp_factor}x")

    async def start_simulation(self):
        """
        Starts the main simulation loop as an asynchronous task.
        """
        if self.running: return
        
        logger.info("Starting simulation...")
        self.running = True
        
        self._simulation_task = asyncio.create_task(self._simulation_loop())

    async def stop_simulation(self):
        """
        Stops the main simulation loop.
        """
        if not self.running: return

        self.running = False
        logger.info("Stopping simulation...")
        self._simulation_task.cancel()

        try:
            await self._simulation_task
        except asyncio.CancelledError:
            logger.debug("Simulation stopped cleanly")

    async def _simulation_loop(self):
        """
        The private, core "heartbeat" loop of the simulation.
        """
        loop = asyncio.get_running_loop()
        next_tick_time = loop.time()

        while self.running:    
            try:
               await self._tick()
            except Exception as e:
                logger.error(f"!!! Simulation Tick Failed: {e}", exc_info=True)
                alert = Alert(level="CRITICAL", message=f"Tick failed: {e}", source="SimulationKernel")
                self.state.alerts.append(alert)

            next_tick_time += self.tick_duration
            sleep_duration = next_tick_time - loop.time()

            if sleep_duration >= 0:
               await asyncio.sleep(sleep_duration)
            else:
                logger.warning("!!! SIMULATION LAG: Tick took too long!")

    async def _tick(self):
        """
        Executes a single, atomic tick of the simulation.
        """
        self.state.alerts.clear()

        time_step_seconds = self.tick_duration * self.time_warp_factor
        self.current_sim_time = self.current_sim_time + (time_step_seconds * u.s)
        timestamp = self.current_sim_time.to_datetime(timezone.utc)

        position, velocity = self.propagator.get_state_at_time(self.current_sim_time)
        
        # --- Phase 1: Orbit ---
        self.state.orbit.position = position
        self.state.orbit.velocity = velocity
        
        # --- Phase 2: Attitude ---
        

        # --- Phase 3: Environment ---
        

        # --- Phase 4: Constraints ---
        

        # --- Broadcast State ---
        self.state.timestamp = timestamp
        await connection_manager.broadcast(self.state)
        

simulation_kernel = SimulationKernel()
