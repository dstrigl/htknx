#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  htknx - TODO
#  Copyright (C) 2020  Daniel Strigl

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

""" TODO """

import logging
import voluptuous as vol
import yaml

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import PhysicalAddress
from htheatpump.htparams import HtParams
from datetime import timedelta
from typing import Dict, Any

import config_validation as cv

_logger = logging.getLogger(__name__)


CONF_GENERAL = "general"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CYCLIC_SENDING_INTERVAL = "cyclic_sending_interval"

CONF_HEAT_PUMP = "heat_pump"
CONF_DEVICE = "device"
CONF_BAUDRATE = "baudrate"
CONF_PARAM_VERIFICATION = "param_verification"

CONF_KNX = "knx"
CONF_GATEWAY_IP = "gateway_ip"
CONF_GATEWAY_PORT = "gateway_port"
CONF_AUTO_RECONNECT = "auto_reconnect"
CONF_AUTO_RECONNECT_WAIT = "auto_reconnect_wait"
CONF_LOCAL_IP = "local_ip"
CONF_OWN_ADDRESS = "own_address"
CONF_RATE_LIMIT = "rate_limit"

CONF_DATA_POINTS = "data_points"
CONF_PARAM_NAME = "param_name"
CONF_VALUE_TYPE = "value_type"
CONF_GROUP_ADDRESS = "group_address"
CONF_WRITABLE = "writable"
CONF_CYCLIC_SENDING = "cyclic_sending"
CONF_SEND_ON_CHANGE = "send_on_change"
CONF_ON_CHANGE_OF = "on_change_of"
# TODO -> on_change_of_relative / on_change_of_absolute

CONF_NOTIFICATIONS = "notifications"
CONF_ON_MALFUNCTION = "on_malfunction"


DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_CYCLIC_SENDING_INTERVAL = 600
DEFAULT_BAUDRATE = 115200
DEFAULT_GATEWAY_PORT = 3671
DEFAULT_AUTO_RECONNECT_WAIT = 3


GENERAL_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
        ): cv.time_interval,  # TODO > 0
        vol.Optional(
            CONF_CYCLIC_SENDING_INTERVAL, default=DEFAULT_CYCLIC_SENDING_INTERVAL
        ): cv.time_interval,  # TODO > 0
    }
)

HEAT_PUMP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.All(
            vol.Coerce(int), vol.In([9600, 19200, 38400, 57600, 115200])
        ),
        vol.Optional(CONF_PARAM_VERIFICATION, default=True): cv.boolean,
    }
)

KNX_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GATEWAY_IP): cv.string,
        vol.Optional(CONF_GATEWAY_PORT, default=DEFAULT_GATEWAY_PORT): cv.port,
        vol.Optional(CONF_AUTO_RECONNECT, default=True): cv.boolean,
        vol.Optional(
            CONF_AUTO_RECONNECT_WAIT, default=DEFAULT_AUTO_RECONNECT_WAIT
        ): cv.time_interval,  # TODO > 0
        vol.Optional(CONF_LOCAL_IP): cv.string,
        vol.Optional(
            CONF_OWN_ADDRESS, default=XKNX.DEFAULT_ADDRESS
        ): cv.ensure_physical_address,
        vol.Optional(CONF_RATE_LIMIT, default=XKNX.DEFAULT_RATE_LIMIT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
    }
)

DATA_POINT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VALUE_TYPE): cv.string,  # TODO validate!
        vol.Required(CONF_GROUP_ADDRESS): cv.ensure_group_address,
        vol.Optional(CONF_WRITABLE, default=False): cv.boolean,
        vol.Optional(CONF_CYCLIC_SENDING, default=False): cv.boolean,
        vol.Optional(CONF_SEND_ON_CHANGE, default=False): cv.boolean,
        vol.Optional(CONF_ON_CHANGE_OF, default=None): vol.Any(cv.number, None),
        # TODO CONF_ON_CHANGE_OF only allowed for data points with value type != 'binary' and 'send_on_change' == True
        # TODO CONF_ON_CHANGE_OF cv.positive_number
        # TODO -> on_change_of_relative / on_change_of_absolute
    }
)

DATA_POINTS_SCHEMA = vol.Schema(
    {vol.All(cv.string, vol.In(HtParams.keys())): DATA_POINT_SCHEMA}
)

NOTIFICATION_SCHEMA = vol.Schema(
    {vol.Required(CONF_GROUP_ADDRESS): cv.ensure_group_address}
)

NOTIFICATIONS_SCHEMA = vol.Schema(
    {CONF_ON_MALFUNCTION: NOTIFICATION_SCHEMA, "on_xyz": NOTIFICATION_SCHEMA}
)

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
            CONF_PARAM_VERIFICATION: True,
        }
        self.knx: Dict[str, Any] = {
            "connection_config": ConnectionConfig(
                connection_type=ConnectionType.TUNNELING
            ),
            CONF_OWN_ADDRESS: PhysicalAddress(XKNX.DEFAULT_ADDRESS),
            CONF_RATE_LIMIT: XKNX.DEFAULT_RATE_LIMIT,
        }
        self.data_points: Dict[str, dict] = {}
        self.notifications: Dict[str, dict] = {}

    def read(self, filename: str = "htknx.yaml") -> None:
        """Read the configuration from the given file.

        :param filename: The filename to read the configuration from, e.g. 'htknx.yaml'.
        :type filename: str
        """
        _logger.debug("reading config file {!r}".format(filename))
        try:
            with open(filename, "r") as f:
                doc = yaml.safe_load(f)
                doc = CONFIG_SCHEMA(doc)
                self._parse_general_settings(doc)
                self._parse_heat_pump_settings(doc)
                self._parse_knx_settings(doc)
                self._parse_data_points(doc)
                self._parse_notifications(doc)
        except Exception as e:
            _logger.error("failed to read config file '{%s}': %s", filename, e)
            raise

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
                ]
            if CONF_LOCAL_IP in doc[CONF_KNX]:
                self.knx["connection_config"].local_ip = doc[CONF_KNX][CONF_LOCAL_IP]
            if CONF_OWN_ADDRESS in doc[CONF_KNX]:
                self.knx[CONF_OWN_ADDRESS] = PhysicalAddress(
                    doc[CONF_KNX][CONF_OWN_ADDRESS]
                )
            if CONF_RATE_LIMIT in doc[CONF_KNX]:
                self.knx[CONF_RATE_LIMIT] = doc[CONF_KNX][CONF_RATE_LIMIT]

    def _parse_data_points(self, doc) -> None:
        """Parse the data points section of the config file."""
        if CONF_DATA_POINTS in doc:
            for name, config in doc[CONF_DATA_POINTS].items():
                self.data_points[name] = config

    def _parse_notifications(self, doc) -> None:
        """Parse the notifications section of the config file."""
        if CONF_NOTIFICATIONS in doc:
            self.notifications.update(doc[CONF_NOTIFICATIONS])
