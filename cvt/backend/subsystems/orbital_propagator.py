from __future__ import annotations

from tletools import TLE
from poliastro.twobody import Orbit
from poliastro.bodies import Earth
import astropy.units as u
from astropy.time import Time
from typing import Tuple

from cvt.config.config import config

import logging

logger = logging.getLogger(__name__)

class OrbitalPropagator:
    """
    A modular "black box" for handling orbital mechanics.
    Its only job is to answer "Where is the satellite right now?"
    """

    def __init__(self):
        """
        Initializes the propagator by loading the TLE data
        from the global config.
        """
        self.orbit: Orbit = self._load_orbit()

    def get_current_state(self) -> Tuple[list[float], list[float]]:
        """
        Calculates the satellite's current position and velocity.
        This is the main function called by the SimulationKernel on every tick.
        """
        current_time = Time.now()
        propagated_orbit = self.orbit.propagate(current_time)

        r, v = propagated_orbit.r.value.tolist(), propagated_orbit.v.value.tolist()

        return r, v

    def _load_orbit(self) -> Orbit:
        """
        Private helper method to parse the TLE data from config and initialize the orbit.
        """
        try:
            name = config.tle.name
            line1 = config.tle.line1
            line2 = config.tle.line2

            tle = TLE.from_lines(name, line1, line2) 
            orbit = tle.to_orbit(Earth)

            logger.info(f"OrbitalPropagator initialized for '{name}'")
            logger.debug(f"Orbit Epoch: {orbit.epoch.iso}")

            return orbit
        except Exception as e:
            logger.critical(f"Failed to load TLE from config! Error: {e}")
            raise