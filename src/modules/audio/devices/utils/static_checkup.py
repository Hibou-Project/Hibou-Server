from src.modules.audio.devices.dante.models import DanteADCDevice
from dataclasses import fields

import dataclasses

SUPPORTED_DEVICES: set[str] = {"DAI2", "1966"}


def check_names(controllers: list[dict]) -> bool:
    """
    Ensure that all controller names and all nested device names are unique.

    Expected structure:
        controllers = [
            {
                "name": str,
                "devices": [
                    {"name": str, ...},
                    ...
                ]
            },
            ...
        ]

    Args:
        controllers (list[dict]): List of controller dictionaries, each containing
            a 'name' and a list of 'devices'.

    Returns:
        bool: True if all controller names are unique AND all device names are unique
        across all controllers, False otherwise.

    Notes:
        - Missing 'name' fields will result in None values being included in the check.
        - Assumes 'devices' is a list; will raise if it is None or malformed.
    """

    controller_names = [item.get("name") for item in controllers]
    devices = [item.get("devices") for item in controllers]
    devices_name = [item.get("name") for sublist in devices for item in sublist]

    controller_names_valid = len(controller_names) == len(set(controller_names))
    devices_name_valid = len(devices_name) == len(set(devices_name))

    return controller_names_valid and devices_name_valid


def check_ports(controllers: list[dict]) -> bool:
    """
    Ensure all devices have unique 'port' fields.

    Args:
        controllers (list[dict]): List of device dictionaries.

    Returns:
        bool: True if all device ports are unique, False otherwise.
    """
    devices = [item.get("devices") for item in controllers]
    ports = [item.get("port") for sublist in devices for item in sublist]
    return len(ports) == len(set(ports))


def check_required_fields(devices, model_cls=DanteADCDevice) -> None:
    """
    Validate that all required fields from a dataclass are present
    in each device dictionary.

    Args:
        devices (list[dict]): List of device dictionaries.
        model_cls (Type): Dataclass defining required fields.

    Raises:
        ValueError: If any required field is missing in any device.
    """
    required_fields = {
        f.name
        for f in fields(model_cls)
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
    }

    for dev in devices:
        if not isinstance(dev, dict):
            raise TypeError(f"Expected dict, got {type(dev)}: {dev}")

        missing = required_fields - dev.keys()
        if missing:
            raise ValueError(
                f"Device '{dev.get('name', '<unknown>')}' is missing fields: {sorted(missing)}"
            )


def check_port_range(devices: list[dict]) -> None:
    """
    Check that each device port is within the valid range (1–65535).

    Args:
        devices (list[dict]): List of device dictionaries.

    Raises:
        ValueError: If a port is missing or out of range.
    """
    for dev in devices:
        if not isinstance(dev, dict):
            raise TypeError(f"Expected dict, got {type(dev)}: {dev}")

        port = dev.get("port")

        if not isinstance(port, int):
            raise ValueError(
                f"Invalid or missing port '{port}' for {dev.get('name', '<unknown>')}"
            )

        if not (1 <= port <= 65535):
            raise ValueError(f"Invalid port {port} for {dev.get('name', '<unknown>')}")


def check_rtp_payload(devices: list[dict]) -> None:
    """
    Check that each device RTP payload is within the dynamic range (96–127).

    Args:
        devices (list[dict]): List of device dictionaries.

    Raises:
        ValueError: If the RTP payload is missing or out of range.
    """
    for dev in devices:
        if not isinstance(dev, dict):
            raise TypeError(f"Expected dict, got {type(dev)}: {dev}")

        payload = dev.get("rtp_payload")

        if not isinstance(payload, int):
            raise ValueError(
                f"Invalid or missing RTP payload '{payload}' for {dev.get('name', '<unknown>')}"
            )

        if not (96 <= payload <= 127):
            raise ValueError(
                f"Invalid RTP payload {payload} for {dev.get('name', '<unknown>')}"
            )


def check_device_model(dev: list[dict]) -> None:
    models = [item.get("model") for item in dev]
    names = [item.get("name", "Unknown device") for item in dev]

    for model, name in zip(models, names):
        if model not in SUPPORTED_DEVICES:
            raise ValueError(
                f"Invalid device model '{model}' for {name}.\n"
                f"Supported models: {', '.join(SUPPORTED_DEVICES)}"
            )


def check_device(dev: list[dict]) -> None:
    """
    Run all validation checks for a single device.

    Args:
        dev (dict): Device dictionary to validate.

    Raises:
        ValueError: If any validation check fails.
    """
    check_device_model(dev)
    check_required_fields(dev)
    check_port_range(dev)
    check_rtp_payload(dev)


def static_checkup(controllers) -> bool:
    """
    Run consistency and validation checks on a list of devices.

    Performs the following checks:
        - All device names are unique.
        - All device ports are unique.
        - Each device contains all required fields.
        - Each device's port is within valid range (1–65535).
        - Each device's RTP payload is within dynamic range (96–127).

    Args:
        controllers (list[dict]): List of device dictionaries to validate.

    Returns:
        bool: True if all checks pass.

    Raises:
        ValueError: If any check fails.
    """

    ok_names = check_names(controllers)
    if not ok_names:
        raise ValueError("Device names must be unique!")

    ok_ports = check_ports(controllers)
    if not ok_ports:
        raise ValueError("Device ports must be unique!")

    for controller in controllers:
        check_device(controller.get("devices"))

    return True
