from .controllers.yamaha.tio1608_d import YamahaTio1608Controller
from .controllers.audinate.avio_ai2 import AvioAi2Controller
from .controllers.base_controller import BaseController
from src.logger import blank_line_module, CustomLogger
from src.helpers.json import read_json, write_json
from .utils.static_checkup import static_checkup
from src.helpers.decorators import singleton
from .dante.models import DanteADCDevice
from typing import List, Dict, Any
from dataclasses import asdict
from pathlib import Path

logger = CustomLogger("audio").get_logger()


@singleton
class ADCControllerManager:
    _SUPPORTED_CONTROLLER: List[BaseController] = [
        YamahaTio1608Controller,
        AvioAi2Controller,
    ]

    def __init__(self):
        self.controllers: List[BaseController] = []

    @property
    def adc_devices(self) -> List[DanteADCDevice]:
        """
        Return a list of DanteADCDevice instances from all controllers.
        """
        _adc_devices: List[DanteADCDevice] = []
        for controller in self.controllers:
            _adc_devices.extend(controller.adc_devices)

        return _adc_devices

    def load_devices_from_files(self, json_path: Path) -> None:
        """
        Load controllers and devices from the controllers_devices.json configuration file.
        Populates self.controllers with controller instances.
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Controller configuration file not found: {json_path}"
            )

        data = read_json(path)
        controllers_data = data.get("controllers", [])
        if not controllers_data:
            raise ValueError("No controllers found in the provided JSON file.")

        if not static_checkup(controllers_data):
            raise ValueError("Updated device configuration failed static validation.")

        loaded_controllers: List[BaseController] = []

        for controller_data in controllers_data:
            controller_name = controller_data.get("name")

            try:
                if controller_name == "AVIOAI2":
                    # AvioAi2Controller takes a list of DanteADCDevice instances
                    devices_data = controller_data.get("devices", [])

                    dante_devices = [DanteADCDevice(**dev) for dev in devices_data]
                    controller = AvioAi2Controller(dante_devices)
                    loaded_controllers.append(controller)
                    logger.info(
                        f"Loaded {controller_name} controller with {len(dante_devices)} devices"
                    )

                elif controller_name == "YamahaTio1608":
                    # YamahaTio1608Controller takes an IP address string
                    # Try to get IP from the controller-level field, or from the first device
                    ip = controller_data.get("ip")
                    devices_data = controller_data.get("devices", [])

                    default_ha_gains = None
                    if controller_data.get("ha_gains"):
                        default_ha_gains = controller_data.get("ha_gains")
                    controller = YamahaTio1608Controller(
                        ip, auto_discovery=False, default_ha_gains=default_ha_gains
                    )

                    # Load devices from the JSON file instead of using scanned devices
                    if devices_data:
                        dante_devices = [DanteADCDevice(**dev) for dev in devices_data]
                        controller.adc_devices = dante_devices
                        logger.info(
                            f"Loaded {controller_name} controller with IP {ip} and {len(dante_devices)} devices from file"
                        )
                    else:
                        logger.warning(
                            f"No devices found for {controller_name} controller"
                        )

                    loaded_controllers.append(controller)

            except Exception as e:
                logger.exception(f"Failed to load controller {controller_name}: {e}")
                continue

        if not loaded_controllers:
            logger.warning(
                "No controllers were successfully loaded from the configuration file."
            )

        self.controllers = loaded_controllers
        logger.info(f"Loaded {len(loaded_controllers)} controllers from {json_path}")

    def save_devices_to_files(self, json_path: Path) -> None:
        """
        Save current controllers and their devices to the controllers_devices.json configuration file.
        """
        if not self.controllers:
            logger.warning("No controllers to save. Skipping file write.")
            return

        controllers_data: List[Dict[str, Any]] = []

        for controller in self.controllers:
            controller_dict: Dict[str, Any] = {}

            if isinstance(controller, AvioAi2Controller):
                controller_dict["name"] = "AVIOAI2"
                # Extract devices from AvioAi2Controller
                devices = controller.adc_devices
                controller_dict["devices"] = [asdict(dev) for dev in devices]

            elif isinstance(controller, YamahaTio1608Controller):
                controller_dict["name"] = "YamahaTio1608"
                # Extract IP from YamahaTio1608Controller
                controller_dict["ip"] = controller.ip
                # Extract devices from YamahaTio1608Controller
                devices = controller.adc_devices
                controller_dict["devices"] = [asdict(dev) for dev in devices]

            else:
                logger.warning(
                    f"Unknown controller type {type(controller).__name__}. Skipping."
                )
                continue

            controllers_data.append(controller_dict)

        if not controllers_data:
            logger.warning("No valid controllers to save. Skipping file write.")
            return

        output_data = {"controllers": controllers_data}
        write_json(json_path, output_data)
        logger.info(
            f"Saved {len(controllers_data)} controllers with "
            f"{sum(len(c.get('devices', [])) for c in controllers_data)} total devices to {json_path}"
        )

    def auto_discover(self):
        """
        Automatically discover devices using all controllers.
        """
        discovered_controllers: List[BaseController] = []
        for manager in self._SUPPORTED_CONTROLLER:
            blank_line_module()
            logger.info(f"Auto-discovering devices for {manager.__name__}")

            try:
                controllers = manager.scan_devices()
                discovered_controllers.extend(controllers)
            except Exception as e:
                logger.exception(
                    f"Failed to auto-discover devices for {manager.__class__.__name__}, {e}",
                )

        if not discovered_controllers:
            logger.warning("No devices discovered on all managers.")

        self.controllers = discovered_controllers

    def __str__(self):
        return f"{self.__class__.__name__}({self.adc_devices})"
