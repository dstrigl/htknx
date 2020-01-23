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

import yaml
import voluptuous as vol
import config_validation as cv
from xknx.knx import PhysicalAddress
from htheatpump.htparams import HtParams

import logging
_logger = logging.getLogger(__name__)


CONF_GENERAL = "general"
CONF_OWN_ADDRESS = "own_address"
CONF_RATE_LIMIT = "rate_limit"
CONF_UPDATE_TIME = "update_time"
CONF_CYCLIC_SENDING_TIME = "cyclic_sending_time"
CONF_CONNECTION = "connection"
CONF_LOCAL_IP = "local_ip"
CONF_GATEWAY_IP = "gateway_ip"
CONF_GATEWAY_PORT = "gateway_port"
CONF_DATA_POINTS = "data_points"
CONF_NAME = "name"
CONF_DATA_TYPE = "data_type"
CONF_GROUP_ADDRESS = "group_address"
CONF_WRITABLE = "writable"
CONF_CYCLIC_SENDING = "cyclic_sending"
CONF_SEND_ON_CHANGE = "send_on_change"
CONF_ON_CHANGE_OF = "on_change_of"

KNX_GA_REGEX = "^(3[0-1]|[1-2]\d|\d)/([0-7])/(2[0-5][0-5]|1\d\d|[1-9]?[0-9])$"  # valid GA: [0-31]/[0-7]/[0-255]
KNX_PA_REGEX = "^(1[0-5]|\d)\.(1[0-5]|\d)\.(2[0-5][0-5]|1\d\d|[1-9]?[0-9])$"  # valid PA: [0-15].[0-15].[0-255]  # TODO


GENERAL_SCHEMA = vol.Schema({
    vol.Optional(CONF_OWN_ADDRESS): cv.matches_regex(KNX_PA_REGEX),
    vol.Optional(CONF_RATE_LIMIT): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional(CONF_UPDATE_TIME): cv.time_interval,
    vol.Optional(CONF_CYCLIC_SENDING_TIME): cv.time_interval,
})

CONNECTION_SCHEMA = vol.Schema({
    vol.Required(CONF_GATEWAY_IP): cv.string,
    vol.Optional(CONF_GATEWAY_PORT): cv.port,
    vol.Optional(CONF_LOCAL_IP): cv.string,
})

DATA_POINT_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): vol.All(cv.string, vol.In(HtParams.keys())),
    vol.Required(CONF_DATA_TYPE): cv.string,  # TODO validate
    vol.Required(CONF_GROUP_ADDRESS): cv.matches_regex(KNX_GA_REGEX),
    vol.Optional(CONF_WRITABLE): cv.boolean,
    vol.Optional(CONF_CYCLIC_SENDING): cv.boolean,
    vol.Optional(CONF_SEND_ON_CHANGE): cv.boolean,
    vol.Optional(CONF_ON_CHANGE_OF): cv.number,
})

CONFIG_SCHEMA = vol.Schema({
    CONF_GENERAL: GENERAL_SCHEMA,
    CONF_CONNECTION: CONNECTION_SCHEMA,
    CONF_DATA_POINTS: [DATA_POINT_SCHEMA],
})
#,extra=vol.ALLOW_EXTRA)  # TODO remove 'extra=vol.ALLOW_EXTRA'


class Config:
    """ Class for parsing a given config file, e.g. 'htknx.yaml'. """

    def __init__(self, htknx) -> None:
        self.htknx = htknx

    def read(self, filename="htknx.yaml") -> None:
        """ Read the configuration from the given file.

        :param filename: The filename to read the configuration from, e.g. 'htknx.yaml'.
        :type filename: str
        """
        _logger.debug("reading config file {!r}".format(filename))
        try:
            with open(filename, 'r') as f:
                doc = yaml.safe_load(f)
                doc = CONFIG_SCHEMA(doc)
                self._parse_general(doc)
                self._parse_connection(doc)
                self._parse_data_points(doc)
        except Exception as e:
            _logger.error("failed to read config file {!r}: {!s}".format(filename, e))
            raise

    def _parse_general(self, doc) -> None:
        """ Parse the general section of the config file. """
        if CONF_GENERAL in doc:
            if CONF_OWN_ADDRESS in doc[CONF_GENERAL]:
                self.htknx.own_address = PhysicalAddress(doc[CONF_GENERAL][CONF_OWN_ADDRESS])
            if CONF_RATE_LIMIT in doc[CONF_GENERAL]:
                self.htknx.rate_limit = doc[CONF_GENERAL][CONF_RATE_LIMIT]
            if CONF_UPDATE_TIME in doc[CONF_GENERAL]:
                self.htknx.publish_interval = doc[CONF_GENERAL][CONF_UPDATE_TIME]

    def _parse_connection(self, doc) -> None:
        """ Parse the connection section of the config file. """
        if CONF_CONNECTION in doc:
            if CONF_LOCAL_IP in doc[CONF_CONNECTION]:
                self.htknx.local_ip = doc[CONF_CONNECTION][CONF_LOCAL_IP]
            if CONF_GATEWAY_IP in doc[CONF_CONNECTION]:
                self.htknx.gateway_ip = doc[CONF_CONNECTION][CONF_GATEWAY_IP]
            if CONF_GATEWAY_PORT in doc[CONF_CONNECTION]:
                self.htknx.gateway_port = doc[CONF_CONNECTION][CONF_GATEWAY_PORT]

    def _parse_data_points(self, doc) -> None:
        """ Parse the data points section of the config file. """
        if CONF_DATA_POINTS in doc:
            for data_point in doc[CONF_DATA_POINTS]:
                print(data_point)
            pass  # TODO


if __name__ == "__main__":
    class ObjTmp:
        pass
    htknx = ObjTmp()
    Config(htknx).read("htknx.yaml")
