from __future__ import annotations

import os
import yaml
import logging
import warnings
from pathlib import Path
from typing import Literal, Any, Dict, Tuple
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent.parent / '.env')
logger = logging.getLogger(__name__)

# --- HELPER FUNCTIONS ---

def get_source_root() -> Path:
    """Returns the absolute path to the project's source root directory."""
    return Path(__file__).parent.parent

def deep_merge(source: dict, destination: dict) -> dict:
    """Recursively merges a source dict into a destination dict."""
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            destination[key] = deep_merge(value, destination[key])
        else:
            destination[key] = value
    return destination

# --- PYDANTIC MODELS: THE SINGLE SOURCE OF TRUTH FOR DEFAULTS ---

class GeneralSettings(BaseModel):
    """General application settings."""
    debug: bool = Field(False, description="Enable verbose debug logging.")
    log_level: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR).")
    supress_user_warnings: bool = Field(True, description="Globally supresses all user warnings.")

class SimulationSettings(BaseModel):
    """Core simulation loop settings."""
    tick_rate_hz: int = Field(10, description="The 'heartbeat' of the simulation in ticks per second.")
    orbit_propagator: str = Field("poliastro_tle", description="Method for orbit calculation.")

class TLESSettings(BaseModel):
    """Default TLE for the 'poliastro_tle' propagator."""
    line1: str = Field("1 25544U 98067A   25299.54407407  .00016717  00000-0  10270-3 0  9997")
    line2: str = Field("2 25544  51.6416 247.4627 0006703 130.5360 325.0158 15.49814673420011")

class FidelitySettings(BaseModel):
    """Flags to enable/disable specific physics models."""
    enable_attitude_dynamics: bool = Field(False)
    enable_atmospheric_drag: bool = Field(False)
    enable_solar_pressure: bool = Field(False)
    enable_gravity_gradient: bool = Field(False)
    enable_magnetic_torque: bool = Field(False)
    enable_adcs_control: bool = Field(False)
    enable_payload_operations: bool = Field(False)

class ConstraintsSettings(BaseModel):
    """Flags to enable/disable hardware constraint emulation."""
    enable_power_budget: bool = Field(False)
    enable_cpu_simulation: bool = Field(False)

class CameraSensorSettings(BaseModel):
    """Emulation settings for the payload's camera sensor."""
    resolution: Tuple[int, int] = Field((640, 480), description="Sensor resolution (width, height).")
    bit_depth: int = Field(8, description="Bit depth of the output image (e.g., 8-bit, 12-bit).")
    noise_level: float = Field(0.0, description="Std deviation of Gaussian noise to add (0.0 to 1.0).")
    blur_level: float = Field(0.0, description="Kernel size for Gaussian blur (0.0 to 5.0).")
    compression_quality: int = Field(95, description="JPEG compression quality (1-100).")

class AIModelSettings(BaseModel):
    """Benchmarked performance metrics for the on-board AI model."""
    inference_time_ms: int = Field(100, description="Measured time for one inference.")
    power_draw_inference_mw: int = Field(150, description="Measured power draw during inference.")
    power_draw_idle_mw: int = Field(10, description="Measured power draw at idle.")
    peak_memory_kb: int = Field(80, description="Measured peak RAM usage during inference.")
    preprocess_time_ms: int = Field(20, description="Time to run pre-processing (e.g., resize).")
    power_draw_preprocess_mw: int = Field(50, description="Power draw during pre-processing.")

class PayloadSettings(BaseModel):
    """Contains all settings for the payload and its components."""
    camera_sensor: CameraSensorSettings = Field(default_factory=CameraSensorSettings)
    ai_model: AIModelSettings = Field(default_factory=AIModelSettings)

class SecretsSettings(BaseModel):
    """Container for API keys and other secrets. Loaded from .env."""
    gee_api_key: str | None = Field(None, description="Google Earth Engine API Key.")
    # Add other keys like Sentinel Hub, etc. here

class CVTConfig(BaseModel):
    """The main configuration object, bringing all settings together."""
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)
    tle: TLESSettings = Field(default_factory=TLESSettings)
    fidelity: FidelitySettings = Field(default_factory=FidelitySettings)
    constraints: ConstraintsSettings = Field(default_factory=ConstraintsSettings)
    payload: PayloadSettings = Field(default_factory=PayloadSettings)
    secrets: SecretsSettings = Field(default_factory=SecretsSettings)

# --- LOGGING SETUP FUNCTION ---

def setup_logging(config: CVTConfig):
    """
    Configures the root logger based on the loaded application settings.
    This function should be called once at application startup.
    """
    root_logger = logging.getLogger()
    log_level_str = config.general.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)-8s] [%(name)s] --- %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    
    logger.debug(f"Root logger configured to level: {log_level_str}")

# --- THE UNIFIED LOADER FUNCTION ---

def load_config(path: str | Path | None = None) -> CVTConfig:
    """
    Loads configuration from YAML and environment variables, providing
    Pydantic defaults for missing values.
    
    Priority: Env Vars > config.yaml > Pydantic Defaults
    """
    config_path = Path(path) if path else get_source_root() / "config/config.yaml"
    
    final_config_dict = CVTConfig().model_dump()
    
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] [%(name)s] %(message)s")

    try:
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            if isinstance(yaml_config, dict):
                final_config_dict = deep_merge(yaml_config, final_config_dict)
                logger.info(f"Loaded configuration from {config_path}")
            else:
                logger.warning(f"Config file at {config_path} is malformed. Using defaults.")
    except FileNotFoundError:
        logger.info(f"Default config file not found at {config_path}. Using defaults.")
    except Exception as e:
        logger.error(f"Error reading YAML config: {e}. Using defaults.")

    env_vars = {
        "general": {
            "debug": os.getenv("CVT_DEBUG"),
            "log_level": os.getenv("CVT_LOG_LEVEL"),
        },
        "simulation": {
            "tick_rate_hz": os.getenv("CVT_SIM_TICK_RATE_HZ")
        },
        "secrets": {
            "gee_api_key": os.getenv("GEE_API_KEY")
        },
        "fidelity": {
            "enable_atmospheric_drag": os.getenv("CVT_ENABLE_ATMOSPHERIC_DRAG")
            # Add other fidelity flags as needed
        }
    }
    
    cleaned_env_vars = {
        k: {k2: v2 for k2, v2 in v.items() if v2 is not None}
        for k, v in env_vars.items() if isinstance(v, dict)
    }
    cleaned_env_vars.update({k: v for k, v in env_vars.items() if not isinstance(v, dict) and v is not None})
    
    final_config_dict = deep_merge(cleaned_env_vars, final_config_dict)

    try:
        config = CVTConfig(**final_config_dict)
        setup_logging(config)
        if config.general.supress_user_warnings:
            warnings.filterwarnings("ignore", category=UserWarning)
        logger.debug("Configuration loaded and validated successfully.")
        return config
    except ValidationError as e:
        config = CVTConfig()
        setup_logging(config)
        logger.error(f"!!! CONFIGURATION VALIDATION ERROR !!!\n{e}\n"
                     "!!! FALLING BACK TO DEFAULT SETTINGS !!!")
        return config

config = load_config()

# --- EXAMPLE USAGE ---
# from cubeSat_virtual_testbed.config.config import config
#
# if config.general.debug:
#     print("Debug mode is ON")
#
# api_key = config.secrets.gee_api_key
