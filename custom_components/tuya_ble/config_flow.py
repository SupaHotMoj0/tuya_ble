"""Config flow for Tuya BLE integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import pycountry
import voluptuous as vol
from tuya_iot import AuthType

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlowWithConfigEntry
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_COUNTRY_CODE,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowHandler, FlowResult

from .const import (
    CONF_ACCESS_ID,
    CONF_ACCESS_SECRET,
    CONF_AUTH_TYPE,
    CONF_ENDPOINT,
    CONF_APP_TYPE,
    DOMAIN,
    SMARTLIFE_APP,
    TUYA_SMART_APP,
    TUYA_COUNTRIES,
    TUYA_RESPONSE_CODE,
    TUYA_RESPONSE_MSG,
    TUYA_RESPONSE_SUCCESS,
)
from .cloud import HASSTuyaBLEDeviceManager
from .devices import TuyaBLEData, get_device_readable_name
from .tuya_ble import SERVICE_UUID, TuyaBLEDeviceCredentials

_LOGGER = logging.getLogger(__name__)


async def _try_login(
    manager: HASSTuyaBLEDeviceManager,
    user_input: Dict[str, Any],
    errors: Dict[str, str],
    placeholders: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Attempt to log in to the Tuya cloud with provided user input."""
    country = next(
        (country for country in TUYA_COUNTRIES if country.name == user_input[CONF_COUNTRY_CODE]),
        None,
    )
    if not country:
        errors["base"] = "invalid_country"
        return None

    data = {
        CONF_ENDPOINT: country.endpoint.value,
        CONF_AUTH_TYPE: AuthType.CUSTOM.value,
        CONF_ACCESS_ID: user_input.get(CONF_ACCESS_ID, ""),
        CONF_ACCESS_SECRET: user_input.get(CONF_ACCESS_SECRET, ""),
        CONF_USERNAME: user_input.get(CONF_USERNAME, ""),
        CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
        CONF_COUNTRY_CODE: country.country_code,
    }

    for app_type in (TUYA_SMART_APP, SMARTLIFE_APP, ""):
        data[CONF_APP_TYPE] = app_type if app_type else SMARTLIFE_APP
        data[CONF_AUTH_TYPE] = AuthType.SMART_HOME.value if app_type else AuthType.CUSTOM.value

        response = await manager._login(data, add_to_cache=True)

        if response.get(TUYA_RESPONSE_SUCCESS, False):
            return data

    errors["base"] = "login_error"
    if response:
        placeholders.update(
            {
                "tuya_response_code": response.get(TUYA_RESPONSE_CODE),
                "tuya_response_msg": response.get(TUYA_RESPONSE_MSG),
            }
        )

    return None


def _show_login_form(
    flow: FlowHandler,
    user_input: Dict[str, Any],
    errors: Dict[str, str],
    placeholders: Dict[str, Any],
) -> FlowResult:
    """Display the Tuya IOT platform login form."""
    if user_input and user_input.get(CONF_COUNTRY_CODE):
        for country in TUYA_COUNTRIES:
            if country.country_code == user_input[CONF_COUNTRY_CODE]:
                user_input[CONF_COUNTRY_CODE] = country.name
                break

    default_country_name: Optional[str] = None
    try:
        def_country = pycountry.countries.get(alpha_2=flow.hass.config.country)
        if def_country:
            default_country_name = def_country.name
    except Exception as e:
        _LOGGER.warning("Error fetching default country: %s", e)

    return flow.async_show_form(
        step_id="login",
        data_schema=vol.Schema(
            {
                vol.Required(
                    CONF_COUNTRY_CODE,
                    default=user_input.get(CONF_COUNTRY_CODE, default_country_name),
                ): vol.In(
                    [country.name for country in TUYA_COUNTRIES]
                ),
                vol.Required(
                    CONF_ACCESS_ID, default=user_input.get(CONF_ACCESS_ID, "")
                ): str,
                vol.Required(
                    CONF_ACCESS_SECRET,
                    default=user_input.get(CONF_ACCESS_SECRET, ""),
                ): str,
                vol.Required(
                    CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")
                ): str,
                vol.Required(
                    CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                ): str,
            }
        ),
        errors=errors,
        description_placeholders=placeholders,
    )


class TuyaBLEOptionsFlow(OptionsFlowWithConfigEntry):
    """Handle a Tuya BLE options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__(config_entry)

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_login(user_input)

    async def async_step_login(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the Tuya IOT platform login step."""
        errors: Dict[str, str] = {}
        placeholders: Dict[str, Any] = {}
        credentials: Optional[TuyaBLEDeviceCredentials] = None
        address: Optional[str] = self.config_entry.data.get(CONF_ADDRESS)

        if user_input:
            domain_data = self.hass.data.get(DOMAIN, {})
            entry_data = domain_data.get(self.config_entry.entry_id)
            if entry_data:
                manager: HASSTuyaBLEDeviceManager = entry_data.get("manager")
                if manager:
                    login_data = await _try_login(
                        manager,
                        user_input,
                        errors,
                        placeholders,
                    )
                    if login_data:
                        credentials = await manager.get_device_credentials(
                            address, force_update=True, save_data=True
                        )
                        if credentials:
                            return self.async_create_entry(
                                title=self.config_entry.title,
                                data=manager.data,
                            )
                        else:
                            errors["base"] = "device_not_registered"

        if not user_input:
            user_input = self.config_entry.options.copy()

        return _show_login_form(self, user_input, errors, placeholders)


class TuyaBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya BLE."""

    VERSION = 1
    CONNECTION_CLASS = ConfigFlow.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._discovery_info: Optional[BluetoothServiceInfoBleak] = None
        self._discovered_devices: Dict[str, BluetoothServiceInfoBleak] = {}
        self._data: Dict[str, Any] = {}
        self._manager: Optional[HASSTuyaBLEDeviceManager] = None
        self._get_device_info_error = False

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info

        if not self._manager:
            self._manager = HASSTuyaBLEDeviceManager(self.hass, self._data)
        await self._manager.build_cache()

        self.context["title_placeholders"] = {
            "name": await get_device_readable_name(discovery_info, self._manager)
        }

        return await self.async_step_login()

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the user step."""
        if not self._manager:
            self._manager = HASSTuyaBLEDeviceManager(self.hass, self._data)
        await self._manager.build_cache()
        return await self.async_step_login(user_input)

    async def async_step_login(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the Tuya IOT platform login step."""
        errors: Dict[str, str] = {}
        placeholders: Dict[str, Any] = {}

        if user_input:
            data = await _try_login(
                self._manager,
                user_input,
                errors,
                placeholders,
            )
            if data:
                self._data.update(data)
                return await self.async_step_device()

        if not user_input:
            user_input = {}
            if self._discovery_info:
                await self._manager.get_device_credentials(
                    self._discovery_info.address,
                    force_update=False,
                    save_data=True,
                )
            if not self._data:
                self._manager.get_login_from_cache()
            if self._data:
                user_input.update(self._data)

        return _show_login_form(self, user_input, errors, placeholders)

    async def async_step_device(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the user step to pick a discovered device."""
        errors: Dict[str, str] = {}

        if user_input:
            address = user_input.get(CONF_ADDRESS)
            discovery_info = self._discovered_devices.get(address)
            if not discovery_info:
                errors["base"] = "invalid_device"
                return self.async_show_form(
                    step_id="device",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_ADDRESS): vol.In(
                                {
                                    info.address: await get_device_readable_name(
                                        info, self._manager
                                    )
                                    for info in self._discovered_devices.values()
                                }
                            )
                        }
                    ),
                    errors=errors,
                )

            local_name = await get_device_readable_name(discovery_info, self._manager)
            await self.async_set_unique_id(discovery_info.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            credentials = await self._manager.get_device_credentials(
                discovery_info.address, force_update=self._get_device_info_error, save_data=True
            )
            self._data[CONF_ADDRESS] = discovery_info.address

            if not credentials:
                self._get_device_info_error = True
                errors["base"] = "device_not_registered"
            else:
                return self.async_create_entry(
                    title=local_name,
                    data={CONF_ADDRESS: discovery_info.address},
                    options=self._data,
                )

        # Discover devices if not already discovered
        if self._discovery_info:
            self._discovered_devices[self._discovery_info.address] = self._discovery_info
        else:
            current_addresses = self._async_current_ids()
            async for discovery in async_discovered_service_info(self.hass):
                if (
                    discovery.address in current_addresses
                    or discovery.address in self._discovered_devices
                    or SERVICE_UUID not in discovery.service_data
                ):
                    continue
                self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_unconfigured_devices")

        # Determine default address
        def_address: Optional[str] = user_input.get(CONF_ADDRESS) if user_input else None
        if not def_address and self._discovered_devices:
            def_address = next(iter(self._discovered_devices))

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS, default=def_address): vol.In(
                        {
                            info.address: await get_device_readable_name(info, self._manager)
                            for info in self._discovered_devices.values()
                        }
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> TuyaBLEOptionsFlow:
        """Get the options flow for this handler."""
        return TuyaBLEOptionsFlow(config_entry)