from __future__ import annotations

import yaml
import logging
import warnings
from pathlib import Path
from typing import Literal, Any, Dict, Tuple, cast

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# --- HELPER FUNCTIONS ---

def get_project_root() -> Path:
    """Returns the absolute path to the project's root directory."""
    return Path(__file__).parent.parent.parent


def yaml_config_settings_source() -> dict[str, Any]:
    """
    A Pydantic-Settings source loader that loads values from our default config.yaml.
    This is loaded *after* .env files but *before* the default model fields.
    """
    config_path = get_project_root() / "cvt" / "config" / "config.yaml"
    
    try:
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            if isinstance(yaml_config, dict):
                logger.debug(f"Successfully loaded default config from {config_path}")
                return yaml_config
            else:
                logger.warning(f"Default config file at {config_path} is malformed. Using defaults.")
                return {}
    except FileNotFoundError:
        logger.warning(f"Default config file not found at {config_path}. Using defaults.")
        return {}
    except Exception as e:
        logger.error(f"Error reading default YAML config: {e}. Using defaults.")
        return {}

class GeneralSettings(BaseModel):
    """General application settings."""
    debug: bool = Field(False, description="Enable verbose debug logging.")
    log_level: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR).")
    supress_user_warnings: bool = Field(True, description="Globally supresses all user warnings.")

class SimulationSettings(BaseModel):
    """Core simulation loop settings."""
    tick_rate_hz: int = Field(10, description="The 'heartbeat' of the simulation in ticks per second.")
    orbit_propagator: str = Field("poliastro_tle", description="Method for orbit calculation.")
    time_warp_factor: float = Field(1.0, description="Simulation speed. 1.0 = real-time, 1000.0 = 1000x real-time.")

class SpaceCraft(BaseModel):
    mass_kg: float = Field(4.5)
    surface_area_m2: float = Field(0.1)
    drag_coefficient: float = Field(2.2)

class TLESSettings(BaseModel):
    """Default TLE for the 'poliastro_tle' propagator."""
    name: str = Field("ISS (ZARYA)")
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


# --- THE MAIN CONFIGURATION OBJECT (BaseSettings) ---

class CVTConfig(BaseSettings):
    """
    The main configuration object, inheriting from BaseSettings to automatically
    load from .env, environment variables, and the YAML file.
    """
    
    # --- Top-level Settings ---
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)
    spacecraft: SpaceCraft = Field(default_factory=SpaceCraft)
    tle: TLESSettings = Field(default_factory=TLESSettings)
    fidelity: FidelitySettings = Field(default_factory=FidelitySettings)
    constraints: ConstraintsSettings = Field(default_factory=ConstraintsSettings)
    payload: PayloadSettings = Field(default_factory=PayloadSettings)
    
    # --- Secrets ---
    GEE_API_KEY: str | None = Field(None)
    SENTINEL_HUB_CLIENT_ID: str | None = Field(None)
    SENTINEL_HUB_CLIENT_SECRET: str | None = Field(None)

    # --- Pydantic-Settings Configuration ---
    model_config = SettingsConfigDict(
        env_file=get_project_root() / ".env",
        env_file_encoding='utf-8',
        
        env_prefix='CVT_',
        
        env_nested_delimiter='_',

        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: "PydanticBaseSettingsSource",
        env_settings: "PydanticBaseSettingsSource",
        dotenv_settings: "PydanticBaseSettingsSource",
        file_secret_settings: "PydanticBaseSettingsSource",
    ) -> tuple["PydanticBaseSettingsSource", ...]:
        """
        Customizes the loading priority to inject the YAML file.
        Priority Order (highest to lowest):
        1. init_settings (runtime arguments)
        2. env_settings (System environment variables)
        3. dotenv_settings (.env file)
        4. yaml_config_settings_source (custom config.yaml loader)
        5. file_secret_settings (Docker secrets, etc.)
        """ 
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_config_settings_source,
            file_secret_settings,
        )

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

# --- GLOBAL SINGLETON LOADER ---

def load_config() -> CVTConfig:
    """
    Loads the configuration singleton.
    """
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] [%(name)s] %(message)s")
    
    try:
        config = CVTConfig()
        
        # --- Finalize Logging Setup ---
        setup_logging(config)
        
        if config.general.supress_user_warnings:
            warnings.filterwarnings("ignore", category=UserWarning)
            
        logger.debug("Configuration loaded and validated successfully.")
        
        if config.general.debug:
            logger.debug("--- FINAL CONFIGURATION ---")
            logger.debug(config.model_dump_json(indent=2))
            logger.debug("---------------------------")
            
        return config
        
    except ValidationError as e:
        logger.error(f"!!! CONFIGURATION VALIDATION ERROR !!!\n{e}\n"
                     f"!!! FALLING BACK TO DEFAULT SETTINGS (WHICH MAY FAIL) !!!")
        config = cast(CVTConfig, CVTConfig.model_construct())
        setup_logging(config)
        return config
    
config = load_config()