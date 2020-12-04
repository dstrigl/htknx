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
from htheatpump.htparams import HtParams
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import PhysicalAddress

import config_validation as cv
from htdatapoint import HtDataPoint

_logger = logging.getLogger(__name__)


CONF_GENERAL = "general"
CONF_OWN_ADDRESS = "own_address"
CONF_RATE_LIMIT = "rate_limit"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CYCLIC_SENDING_INTERVAL = "cyclic_sending_interval"
CONF_CONNECTION = "connection"
CONF_LOCAL_IP = "local_ip"
CONF_GATEWAY_IP = "gateway_ip"
CONF_GATEWAY_PORT = "gateway_port"
CONF_AUTO_RECONNECT = "auto_reconnect"
CONF_AUTO_RECONNECT_WAIT = "auto_reconnect_wait"
CONF_DATA_POINTS = "data_points"
CONF_PARAM_NAME = "param_name"
CONF_DATA_TYPE = "data_type"
CONF_GROUP_ADDRESS = "group_address"
CONF_WRITABLE = "writable"
CONF_CYCLIC_SENDING = "cyclic_sending"
CONF_SEND_ON_CHANGE = "send_on_change"
CONF_ON_CHANGE_OF = "on_change_of"
CONF_NOTIFICATIONS = "notifications"
CONF_ON_MALFUNCTION = "on_malfunction"

DEFAULT_GATEWAY_PORT = 3671


GENERAL_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_OWN_ADDRESS): cv.ensure_physical_address,
        vol.Optional(CONF_RATE_LIMIT, default=20): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(CONF_UPDATE_INTERVAL, default=30): cv.time_interval,
        vol.Optional(CONF_CYCLIC_SENDING_INTERVAL, default=300): cv.time_interval,
    }
)

CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GATEWAY_IP): cv.string,
        vol.Optional(CONF_GATEWAY_PORT, default=DEFAULT_GATEWAY_PORT): cv.port,
        vol.Optional(CONF_LOCAL_IP): cv.string,
        vol.Optional(CONF_AUTO_RECONNECT, default=False): cv.boolean,
        vol.Optional(CONF_AUTO_RECONNECT_WAIT, default=3): cv.time_interval,
    }
)

DATA_POINT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DATA_TYPE): cv.string,  # TODO validate!
        vol.Required(CONF_GROUP_ADDRESS): cv.ensure_group_address,
        vol.Optional(CONF_WRITABLE): cv.boolean,
        vol.Optional(CONF_CYCLIC_SENDING): cv.boolean,
        vol.Optional(CONF_SEND_ON_CHANGE): cv.boolean,
        vol.Optional(CONF_ON_CHANGE_OF): cv.number,
        # TODO on_change_of_relative / on_change_of_absolute
    }
)

DATA_POINTS_SCHEMA = vol.Schema(
    {vol.All(cv.string, vol.In(HtParams.keys())): DATA_POINT_SCHEMA}
)

NOTIFICATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GROUP_ADDRESS): cv.ensure_group_address,
    }
)

NOTIFICATIONS_SCHEMA = vol.Schema(
    {
        CONF_ON_MALFUNCTION: NOTIFICATION_SCHEMA,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        CONF_GENERAL: GENERAL_SCHEMA,
        CONF_CONNECTION: CONNECTION_SCHEMA,
        CONF_DATA_POINTS: DATA_POINTS_SCHEMA,
        vol.Optional(CONF_NOTIFICATIONS): NOTIFICATIONS_SCHEMA,
    }
)
# ,extra=vol.ALLOW_EXTRA)  # TODO remove 'extra=vol.ALLOW_EXTRA'


class Config:
    """ Class for parsing a given config file, e.g. 'htknx.yaml'. """

    def __init__(self, xknx) -> None:
        self.xknx = xknx

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
                self._parse_general(doc)
                self._parse_connection(doc)
                self._parse_data_points(doc)
        except Exception as e:
            _logger.error("failed to read config file '{%s}': %s", filename, e)
            raise

    def _parse_general(self, doc) -> None:
        """ Parse the general section of the config file. """
        if CONF_GENERAL in doc:
            if CONF_OWN_ADDRESS in doc[CONF_GENERAL]:
                self.xknx.own_address = PhysicalAddress(
                    doc[CONF_GENERAL][CONF_OWN_ADDRESS]
                )
                print(f"own_address: {self.xknx.own_address}")
            if CONF_RATE_LIMIT in doc[CONF_GENERAL]:
                self.xknx.rate_limit = doc[CONF_GENERAL][CONF_RATE_LIMIT]
                print(f"rate_limit: {self.xknx.rate_limit}")
            if CONF_UPDATE_INTERVAL in doc[CONF_GENERAL]:
                self.xknx.update_interval = doc[CONF_GENERAL][CONF_UPDATE_INTERVAL]
                print(f"update_interval: {self.xknx.update_interval}")
            if CONF_CYCLIC_SENDING_INTERVAL in doc[CONF_GENERAL]:
                self.xknx.publish_interval = doc[CONF_GENERAL][
                    CONF_CYCLIC_SENDING_INTERVAL
                ]
                print(f"publish_interval: {self.xknx.publish_interval}")

    def _parse_connection(self, doc) -> None:
        """ Parse the connection section of the config file. """
        connection_config = ConnectionConfig(connection_type=ConnectionType.TUNNELING)
        if CONF_CONNECTION in doc:
            if CONF_LOCAL_IP in doc[CONF_CONNECTION]:
                connection_config.local_ip = doc[CONF_CONNECTION][CONF_LOCAL_IP]
                print(f"local_ip: {connection_config.local_ip}")
            if CONF_GATEWAY_IP in doc[CONF_CONNECTION]:
                connection_config.gateway_ip = doc[CONF_CONNECTION][CONF_GATEWAY_IP]
                print(f"gateway_ip: {connection_config.gateway_ip}")
            if CONF_GATEWAY_PORT in doc[CONF_CONNECTION]:
                connection_config.gateway_port = doc[CONF_CONNECTION][CONF_GATEWAY_PORT]
                print(f"gateway_port: {connection_config.gateway_port}")
            if CONF_AUTO_RECONNECT in doc[CONF_CONNECTION]:
                connection_config.auto_reconnect = doc[CONF_CONNECTION][
                    CONF_AUTO_RECONNECT
                ]
                print(f"auto_reconnect: {connection_config.auto_reconnect}")
            if CONF_AUTO_RECONNECT_WAIT in doc[CONF_CONNECTION]:
                connection_config.auto_reconnect_wait = doc[CONF_CONNECTION][
                    CONF_AUTO_RECONNECT_WAIT
                ]
                print(f"auto_reconnect_wait: {connection_config.auto_reconnect_wait}")
            self.xknx.connection_config = connection_config

    def _parse_data_points(self, doc) -> None:
        """ Parse the data points section of the config file. """
        if CONF_DATA_POINTS in doc:
            print(f"{CONF_DATA_POINTS}:")
            for name, config in doc[CONF_DATA_POINTS].items():
                print(f"\t'{name}':")
                print(f"\t\t{config}")
                HtDataPoint.from_config(self.xknx, name, config)


if __name__ == "__main__":

    class ObjTmp:
        pass

    xknx = ObjTmp()
    Config(xknx).read("htknx.yaml")
