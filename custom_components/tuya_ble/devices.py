"""Tuya BLE devices module for Home Assistant integration.

This module handles:
1. BLE device discovery and registration checks (both locally and in Tuya Cloud).
2. Entity creation and updates via Home Assistant's Coordinator pattern.
3. Displaying and logging both full and short MAC addresses for better diagnostics.
4. Maintaining consistency of device metadata (e.g., name, manufacturer, model).
5. Providing improved error handling and debug logging.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass

from homeassistant.const import CONF_ADDRESS, CONF_DEVICE_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import (
    DeviceInfo,
    EntityDescription,
    generate_entity_id,
)
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from home_assistant_bluetooth import BluetoothServiceInfoBleak

from .tuya_ble import (
    AbstaractTuyaBLEDeviceManager,
    TuyaBLEDataPoint,
    TuyaBLEDevice,
    TuyaBLEDeviceCredentials,
)

from .cloud import HASSTuyaBLEDeviceManager
from .const import (
    DEVICE_DEF_MANUFACTURER,
    DOMAIN,
    FINGERBOT_BUTTON_EVENT,
    SET_DISCONNECTED_DELAY,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class TuyaBLEFingerbotInfo:
    """Data structure to represent a Fingerbot device's DP mappings."""
    switch: int
    mode: int
    up_position: int
    down_position: int
    hold_time: int
    reverse_positions: int
    manual_control: int = 0
    program: int = 0


@dataclass
class TuyaBLEProductInfo:
    """Information about a Tuya BLE product."""
    name: str
    manufacturer: str = DEVICE_DEF_MANUFACTURER
    fingerbot: TuyaBLEFingerbotInfo | None = None


@dataclass
class TuyaBLECategoryInfo:
    """Collection of product info objects for a given category."""
    products: dict[str, TuyaBLEProductInfo]
    info: TuyaBLEProductInfo | None = None


@dataclass
class TuyaBLEData:
    """Data for the Tuya BLE integration."""
    title: str
    device: TuyaBLEDevice
    product: TuyaBLEProductInfo
    manager: HASSTuyaBLEDeviceManager
    coordinator: "TuyaBLECoordinator"


# Database of known Tuya BLE devices, keyed by category + product_id
devices_database: dict[str, TuyaBLECategoryInfo] = {
    "co2bj": TuyaBLECategoryInfo(
        products={
            "59s19z5m": TuyaBLEProductInfo(  # device product_id
                name="CO2 Detector",
            ),
        },
    ),
    "ms": TuyaBLECategoryInfo(
        products={
            **dict.fromkeys(
                [
                    "ludzroix",
                    "isk2p555",
                    "isljqiq1"
                ],
                TuyaBLEProductInfo(
                    name="Smart Lock",
                ),
            ),
        },
    ),
    "szjqr": TuyaBLECategoryInfo(
        products={
            "3yqdo5yt": TuyaBLEProductInfo(
                name="CUBETOUCH 1s",
                fingerbot=TuyaBLEFingerbotInfo(
                    switch=1,
                    mode=2,
                    up_position=5,
                    down_position=6,
                    hold_time=3,
                    reverse_positions=4,
                ),
            ),
            "xhf790if": TuyaBLEProductInfo(
                name="CubeTouch II",
                fingerbot=TuyaBLEFingerbotInfo(
                    switch=1,
                    mode=2,
                    up_position=5,
                    down_position=6,
                    hold_time=3,
                    reverse_positions=4,
                ),
            ),
            **dict.fromkeys(
                [
                    "blliqpsj",
                    "ndvkgsrm",
                    "yiihr7zh",
                    "neq16kgd"
                ],
                TuyaBLEProductInfo(
                    name="Fingerbot Plus",
                    fingerbot=TuyaBLEFingerbotInfo(
                        switch=2,
                        mode=8,
                        up_position=15,
                        down_position=9,
                        hold_time=10,
                        reverse_positions=11,
                        manual_control=17,
                        program=121,
                    ),
                ),
            ),
            **dict.fromkeys(
                [
                    "ltak7e1p",
                    "y6kttvd6",
                    "yrnk7mnn",
                    "nvr2rocq",
                    "bnt7wajf",
                    "rvdceqjh",
                    "5xhbk964",
                ],
                TuyaBLEProductInfo(
                    name="Fingerbot",
                    fingerbot=TuyaBLEFingerbotInfo(
                        switch=2,
                        mode=8,
                        up_position=15,
                        down_position=9,
                        hold_time=10,
                        reverse_positions=11,
                        program=121,
                    ),
                ),
            ),
        },
    ),
    "wk": TuyaBLECategoryInfo(
        products={
            **dict.fromkeys(
                [
                    "drlajpqc",
                    "nhj2j7su",
                ],
                TuyaBLEProductInfo(
                    name="Thermostatic Radiator Valve",
                ),
            ),
        },
    ),
    "wsdcg": TuyaBLECategoryInfo(
        products={
            "ojzlzzsw": TuyaBLEProductInfo(
                name="Soil moisture sensor",
            ),
        },
    ),
    "znhsb": TuyaBLECategoryInfo(
        products={
            "cdlandip": TuyaBLEProductInfo(
                name="Smart water bottle",
            ),
        },
    ),
    "ggq": TuyaBLECategoryInfo(
        products={
            "6pahkcau": TuyaBLEProductInfo(
                name="Irrigation computer",
            ),
        },
    ),
}


def get_product_info_by_ids(
    category: str, product_id: str
) -> TuyaBLEProductInfo | None:
    """Lookup TuyaBLEProductInfo for a given category + product_id."""
    category_info = devices_database.get(category)
    if not category_info:
        return None

    # If the product is found by exact match, return it
    product_info = category_info.products.get(product_id)
    if product_info is not None:
        return product_info

    # Otherwise, default to the category-level info
    return category_info.info


def get_full_address(address: str) -> str:
    """Return the full BLE address in uppercase hex form."""
    return address.replace("-", ":").upper()


def get_short_address(address: str) -> str:
    """Return a shortened form of the BLE address (last three bytes).
    
    E.g. 'AA:BB:CC:DD:EE:FF' -> 'DD:EE:FF'
    """
    full = get_full_address(address)
    parts = full.split(":")
    # Return only the last 3 sets, e.g. 'DD:EE:FF'
    return ":".join(parts[-3:])


async def get_device_readable_name(
    discovery_info: BluetoothServiceInfoBleak,
    manager: AbstaractTuyaBLEDeviceManager | None,
) -> str:
    """Construct a user-friendly name for the discovered device.

    This function attempts to fetch the device credentials from the manager
    to determine category/product names. If found, it includes them in the name.

    Includes both short and full BLE MAC in the final string for clarity.
    """
    credentials: TuyaBLEDeviceCredentials | None = None
    product_info: TuyaBLEProductInfo | None = None

    full_mac = get_full_address(discovery_info.address)
    short_mac = get_short_address(discovery_info.address)

    # Log the full MAC for diagnostic purposes
    _LOGGER.debug("Discovered device with full MAC: %s, short MAC: %s", full_mac, short_mac)

    if manager:
        try:
            credentials = await manager.get_device_credentials(discovery_info.address)
        except Exception as err:
            _LOGGER.warning(
                "Error retrieving device credentials for %s (%s): %s",
                full_mac, short_mac, err
            )

        if credentials:
            product_info = get_product_info_by_ids(
                credentials.category,
                credentials.product_id,
            )

    # Create a fallback name from the BLE advertisement if nothing else is found
    fallback_name = discovery_info.device.name or "Unknown BLE Device"

    if product_info:
        # Combine product name, fallback, and both MAC forms
        return f"{product_info.name} ({fallback_name}) [Full MAC: {full_mac}, Short: {short_mac}]"
    if credentials:
        # Combine credentials device name, fallback, and both MAC forms
        return f"{credentials.device_name} ({fallback_name}) [Full MAC: {full_mac}, Short: {short_mac}]"

    # If we have neither product info nor credentials, just show the fallback name
    return f"{fallback_name} [Full MAC: {full_mac}, Short: {short_mac}]"


def get_device_product_info(device: TuyaBLEDevice) -> TuyaBLEProductInfo | None:
    """Retrieve the product info from the local database for the given device."""
    return get_product_info_by_ids(device.category, device.product_id)


def get_device_info(device: TuyaBLEDevice) -> DeviceInfo:
    """Build a DeviceInfo object for registering the device in Home Assistant.

    Includes both short and full MAC addresses for improved diagnostics,
    plus manufacturer/product info if available.
    """
    product_info = get_device_product_info(device)
    product_name = product_info.name if product_info else device.name
    manufacturer = (
        product_info.manufacturer if product_info else DEVICE_DEF_MANUFACTURER
    )

    full_mac = get_full_address(device.address)
    short_mac = get_short_address(device.address)

    # Log the device info build process
    _LOGGER.debug(
        "Building device info for device_id=%s: name='%s', manufacturer='%s', "
        "full_mac='%s', short_mac='%s'",
        device.device_id, product_name, manufacturer, full_mac, short_mac
    )

    return DeviceInfo(
        connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        hw_version=device.hardware_version,
        identifiers={(DOMAIN, device.address)},
        manufacturer=manufacturer,
        model=f"{device.product_model or product_name} ({device.product_id})",
        # Append both short and full MAC in the display name
        name=f"{product_name} [Full MAC: {full_mac}, Short: {short_mac}]",
        sw_version=f"{device.device_version} (protocol {device.protocol_version})",
    )


class TuyaBLECoordinator(DataUpdateCoordinator[None]):
    """Data coordinator for receiving and handling Tuya BLE updates."""

    def __init__(self, hass: HomeAssistant, device: TuyaBLEDevice) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self._device = device
        self._disconnected: bool = True
        self._unsub_disconnect: CALLBACK_TYPE | None = None

        device.register_connected_callback(self._async_handle_connect)
        device.register_callback(self._async_handle_update)
        device.register_disconnected_callback(self._async_handle_disconnect)

        _LOGGER.debug(
            "TuyaBLECoordinator created for device %s (%s)",
            device.device_id,
            get_full_address(device.address),
        )

    @property
    def connected(self) -> bool:
        """Return True if the device is currently connected."""
        return not self._disconnected

    @callback
    def _async_handle_connect(self) -> None:
        """Handle device connected callback."""
        if self._unsub_disconnect is not None:
            self._unsub_disconnect()
        if self._disconnected:
            self._disconnected = False
            _LOGGER.debug(
                "Device connected: %s (%s)",
                self._device.device_id,
                get_full_address(self._device.address),
            )
            self.async_update_listeners()

    @callback
    def _async_handle_update(self, updates: list[TuyaBLEDataPoint]) -> None:
        """Handle data updates from the device."""
        self._async_handle_connect()
        self.async_set_updated_data(None)  # Not passing any structured data

        info = get_device_product_info(self._device)
        if info and info.fingerbot and info.fingerbot.manual_control != 0:
            for update in updates:
                if update.id == info.fingerbot.switch and update.changed_by_device:
                    # Fire a Home Assistant event for fingerbot button press
                    self.hass.bus.fire(
                        FINGERBOT_BUTTON_EVENT,
                        {
                            CONF_ADDRESS: self._device.address,
                            CONF_DEVICE_ID: self._device.device_id,
                        },
                    )

    @callback
    def _set_disconnected(self, _: None) -> None:
        """Timeout callback to mark device as disconnected."""
        self._disconnected = True
        self._unsub_disconnect = None
        _LOGGER.debug(
            "Device disconnected due to inactivity: %s (%s)",
            self._device.device_id,
            get_full_address(self._device.address),
        )
        self.async_update_listeners()

    @callback
    def _async_handle_disconnect(self) -> None:
        """Immediately start the countdown to mark device as disconnected."""
        if self._unsub_disconnect is None:
            delay: float = SET_DISCONNECTED_DELAY
            _LOGGER.debug(
                "Device signaled disconnection. Will confirm in %s seconds: %s (%s)",
                delay,
                self._device.device_id,
                get_full_address(self._device.address),
            )
            self._unsub_disconnect = async_call_later(
                self.hass, delay, self._set_disconnected
            )


class TuyaBLEEntity(CoordinatorEntity):
    """Tuya BLE base entity that automatically updates from the coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TuyaBLECoordinator,
        device: TuyaBLEDevice,
        product: TuyaBLEProductInfo,
        description: EntityDescription,
    ) -> None:
        """Initialize the TuyaBLE Entity."""
        super().__init__(coordinator)
        self._hass = hass
        self._coordinator = coordinator
        self._device = device
        self._product = product

        if description.translation_key is None:
            self._attr_translation_key = description.key

        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_device_info = get_device_info(self._device)
        self._attr_unique_id = f"{self._device.device_id}-{description.key}"

        # Use generate_entity_id to ensure consistent entity naming
        self.entity_id = generate_entity_id(
            "sensor.{}", self._attr_unique_id, hass=hass
        )

        _LOGGER.debug(
            "Created TuyaBLEEntity: device_id=%s, unique_id=%s, entity_id=%s",
            self._device.device_id,
            self._attr_unique_id,
            self.entity_id
        )

    @property
    def available(self) -> bool:
        """Return True if entity is currently available (connected)."""
        return self._coordinator.connected

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
