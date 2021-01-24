#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  htknx - Heliotherm heat pump KNX gateway
#  Copyright (C) 2021  Daniel Strigl

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Parsing a given config file in YAML format. """

import logging
from datetime import timedelta
from typing import Any, Callable, Dict

import voluptuous as vol
import yaml
from htheatpump.htparams import HtParams
from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import IndividualAddress

from . import config_validation as cv

_LOGGER = logging.getLogger(__name__)


CONF_GENERAL = "general"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CYCLIC_SENDING_INTERVAL = "cyclic_sending_interval"

CONF_HEAT_PUMP = "heat_pump"
CONF_DEVICE = "device"
CONF_BAUDRATE = "baudrate"

CONF_KNX = "knx"
CONF_GATEWAY_IP = "gateway_ip"
CONF_GATEWAY_PORT = "gateway_port"
CONF_AUTO_RECONNECT = "auto_reconnect"
CONF_AUTO_RECONNECT_WAIT = "auto_reconnect_wait"
CONF_LOCAL_IP = "local_ip"
CONF_OWN_ADDRESS = "own_address"
CONF_RATE_LIMIT = "rate_limit"

CONF_DATA_POINTS = "data_points"
CONF_VALUE_TYPE = "value_type"
CONF_GROUP_ADDRESS = "group_address"
CONF_WRITABLE = "writable"
CONF_CYCLIC_SENDING = "cyclic_sending"
CONF_SEND_ON_CHANGE = "send_on_change"
CONF_ON_CHANGE_OF_ABSOLUTE = "on_change_of_absolute"
CONF_ON_CHANGE_OF_RELATIVE = "on_change_of_relative"

CONF_NOTIFICATIONS = "notifications"
CONF_ON_MALFUNCTION = "on_malfunction"
CONF_REPEAT_AFTER = "repeat_after"


DEFAULT_UPDATE_INTERVAL = 60
DEFAULT_CYCLIC_SENDING_INTERVAL = 600
DEFAULT_BAUDRATE = 115200
DEFAULT_GATEWAY_PORT = 3671
DEFAULT_AUTO_RECONNECT_WAIT = 3
DEFAULT_RATE_LIMIT = 10  # XKNX.DEFAULT_RATE_LIMIT


GENERAL_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
        ): cv.time_interval,
        vol.Optional(
            CONF_CYCLIC_SENDING_INTERVAL, default=DEFAULT_CYCLIC_SENDING_INTERVAL
        ): cv.time_interval,
    }
)

HEAT_PUMP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.All(
            vol.Coerce(int), vol.In([9600, 19200, 38400, 57600, 115200])
        ),
    }
)

KNX_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GATEWAY_IP): cv.string,
        vol.Optional(CONF_GATEWAY_PORT, default=DEFAULT_GATEWAY_PORT): cv.port,
        vol.Optional(CONF_AUTO_RECONNECT, default=True): cv.boolean,
        vol.Optional(
            CONF_AUTO_RECONNECT_WAIT, default=DEFAULT_AUTO_RECONNECT_WAIT
        ): cv.time_interval,
        vol.Optional(CONF_LOCAL_IP): cv.string,
        vol.Optional(
            CONF_OWN_ADDRESS, default=XKNX.DEFAULT_ADDRESS
        ): cv.ensure_individual_address,
        vol.Optional(CONF_RATE_LIMIT, default=DEFAULT_RATE_LIMIT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
    }
)


def validate_data_point() -> Callable:
    """Ensure that the data point is valid."""

    def validate(obj: Dict) -> Dict:
        if (
            obj[CONF_VALUE_TYPE] == "binary"
            and len({CONF_ON_CHANGE_OF_ABSOLUTE, CONF_ON_CHANGE_OF_RELATIVE} & set(obj))
            > 0
        ):
            raise vol.Invalid(
                "{} not allowed for binary data point".format(
                    ", ".join((CONF_ON_CHANGE_OF_ABSOLUTE, CONF_ON_CHANGE_OF_RELATIVE))
                )
            )
        if (
            obj[CONF_VALUE_TYPE] != "binary"
            and obj[CONF_SEND_ON_CHANGE]
            and len({CONF_ON_CHANGE_OF_ABSOLUTE, CONF_ON_CHANGE_OF_RELATIVE} & set(obj))
            < 1
        ):
            raise vol.Invalid(
                "must contain at least one of {}".format(
                    ", ".join((CONF_ON_CHANGE_OF_ABSOLUTE, CONF_ON_CHANGE_OF_RELATIVE))
                )
            )

        return obj

    return validate


DATA_POINT_SCHEMA = vol.All(
    dict,
    vol.Schema(
        {
            vol.Required(CONF_VALUE_TYPE): vol.Or(cv.ensure_knx_dpt, "binary"),
            vol.Required(CONF_GROUP_ADDRESS): cv.ensure_group_address,
            vol.Optional(CONF_WRITABLE, default=False): cv.boolean,
            vol.Optional(CONF_CYCLIC_SENDING, default=False): cv.boolean,
            vol.Optional(CONF_SEND_ON_CHANGE, default=False): cv.boolean,
            vol.Exclusive(
                CONF_ON_CHANGE_OF_ABSOLUTE,
                "on_change_of",
                msg="absolute or relative change",
            ): cv.number_greater_zero,
            vol.Exclusive(
                CONF_ON_CHANGE_OF_RELATIVE,
                "on_change_of",
                msg="absolute or relative change",
            ): cv.number_greater_zero,
        }
    ),
    validate_data_point(),
)


def check_for_valid_parameter_names() -> Callable:
    """Check for valid parameter names in the data points section."""

    def validate(obj: Dict) -> Dict:
        for name in obj.keys():
            if name not in HtParams.keys():
                raise vol.Invalid(f"{name!r} is not a valid heat pump parameter")

        return obj

    return validate


def check_for_warnings_in_data_points() -> Callable:
    """Check for warnings in the data point config section."""

    def validate(obj: Dict) -> Dict:
        for name, dp in obj.items():
            if (
                dp[CONF_VALUE_TYPE] != "binary"
                and not dp[CONF_SEND_ON_CHANGE]
                and len(
                    {CONF_ON_CHANGE_OF_ABSOLUTE, CONF_ON_CHANGE_OF_RELATIVE} & set(dp)
                )
                > 0
            ):
                _LOGGER.warning(
                    "%s is defined, but %s is set to false for data point '%s'",
                    CONF_ON_CHANGE_OF_ABSOLUTE
                    if CONF_ON_CHANGE_OF_ABSOLUTE in dp
                    else CONF_ON_CHANGE_OF_RELATIVE,
                    CONF_SEND_ON_CHANGE,
                    name,
                )

        return obj

    return validate


DATA_POINTS_SCHEMA = vol.All(
    dict,
    vol.Schema({cv.string: DATA_POINT_SCHEMA}),
    check_for_valid_parameter_names(),
    check_for_warnings_in_data_points(),
)

NOTIFICATION_SCHEMA = vol.Schema(
    {vol.Required(CONF_GROUP_ADDRESS): cv.ensure_group_address}
)

ON_MALFUNCTION_SCHEMA = NOTIFICATION_SCHEMA.extend(
    {
        vol.Optional(CONF_REPEAT_AFTER, default=None): vol.Or(cv.time_interval, None),
    }
)

NOTIFICATIONS_SCHEMA = vol.Schema({CONF_ON_MALFUNCTION: ON_MALFUNCTION_SCHEMA})

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_GENERAL): GENERAL_SCHEMA,
        CONF_HEAT_PUMP: HEAT_PUMP_SCHEMA,
        CONF_KNX: KNX_SCHEMA,
        vol.Optional(CONF_DATA_POINTS): DATA_POINTS_SCHEMA,
        vol.Optional(CONF_NOTIFICATIONS): NOTIFICATIONS_SCHEMA,
    }
)


class Config:
    """Class for parsing a given config file, e.g. 'htknx.yaml'."""

    def __init__(self) -> None:
        """Initialize the Config class."""
        self.general: Dict[str, Any] = {
            CONF_UPDATE_INTERVAL: timedelta(DEFAULT_UPDATE_INTERVAL),
            CONF_CYCLIC_SENDING_INTERVAL: timedelta(DEFAULT_CYCLIC_SENDING_INTERVAL),
        }
        self.heat_pump: Dict[str, Any] = {
            CONF_DEVICE: None,
            CONF_BAUDRATE: DEFAULT_BAUDRATE,
        }
        self.knx: Dict[str, Any] = {
            "connection_config": ConnectionConfig(
                connection_type=ConnectionType.TUNNELING
            ),
            CONF_OWN_ADDRESS: IndividualAddress(XKNX.DEFAULT_ADDRESS),
            CONF_RATE_LIMIT: DEFAULT_RATE_LIMIT,
        }
        self.data_points: Dict[str, dict] = {}
        self.notifications: Dict[str, dict] = {}

    def read(self, filename: str = "htknx.yaml") -> None:
        """Read the configuration from the given file.

        :param filename: The filename to read the configuration from, e.g. 'htknx.yaml'.
        :type filename: str
        """
        # _LOGGER.debug("Reading config file '%s'.", filename)
        with open(filename, "r") as f:
            doc = yaml.safe_load(f)
            doc = CONFIG_SCHEMA(doc)
            self._parse_general_settings(doc)
            self._parse_heat_pump_settings(doc)
            self._parse_knx_settings(doc)
            self._parse_data_points(doc)
            self._parse_notifications(doc)

    def _parse_general_settings(self, doc) -> None:
        """Parse the general section of the config file."""
        if CONF_GENERAL in doc:
            self.general.update(doc[CONF_GENERAL])

    def _parse_heat_pump_settings(self, doc) -> None:
        """Parse the heat pump section of the config file."""
        if CONF_HEAT_PUMP in doc:
            self.heat_pump.update(doc[CONF_HEAT_PUMP])

    def _parse_knx_settings(self, doc) -> None:
        """Parse the KNX section of the config file."""
        if CONF_KNX in doc:
            if CONF_GATEWAY_IP in doc[CONF_KNX]:
                self.knx["connection_config"].gateway_ip = doc[CONF_KNX][
                    CONF_GATEWAY_IP
                ]
            if CONF_GATEWAY_PORT in doc[CONF_KNX]:
                self.knx["connection_config"].gateway_port = doc[CONF_KNX][
                    CONF_GATEWAY_PORT
                ]
            if CONF_AUTO_RECONNECT in doc[CONF_KNX]:
                self.knx["connection_config"].auto_reconnect = doc[CONF_KNX][
                    CONF_AUTO_RECONNECT
                ]
            if CONF_AUTO_RECONNECT_WAIT in doc[CONF_KNX]:
                self.knx["connection_config"].auto_reconnect_wait = doc[CONF_KNX][
                    CONF_AUTO_RECONNECT_WAIT
                ].total_seconds()
            if CONF_LOCAL_IP in doc[CONF_KNX]:
                self.knx["connection_config"].local_ip = doc[CONF_KNX][CONF_LOCAL_IP]
            if CONF_OWN_ADDRESS in doc[CONF_KNX]:
                self.knx[CONF_OWN_ADDRESS] = IndividualAddress(
                    doc[CONF_KNX][CONF_OWN_ADDRESS]
                )
            if CONF_RATE_LIMIT in doc[CONF_KNX]:
                self.knx[CONF_RATE_LIMIT] = doc[CONF_KNX][CONF_RATE_LIMIT]

    def _parse_data_points(self, doc) -> None:
        """Parse the data points section of the config file."""
        if CONF_DATA_POINTS in doc:
            self.data_points.update(doc[CONF_DATA_POINTS])

    def _parse_notifications(self, doc) -> None:
        """Parse the notifications section of the config file."""
        if CONF_NOTIFICATIONS in doc:
            self.notifications.update(doc[CONF_NOTIFICATIONS])
