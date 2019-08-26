#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" TODO """

from xknx.devices import Device
from xknx.devices.remote_value_sensor import RemoteValueSensor
from xknx.devices.remote_value_switch import RemoteValueSwitch
#from ??? import ht_heatpump  # type: ignore

#import logging
#_logger = logging.getLogger(__name__)


class HtHeatpumpParam(Device):
    """ TODO """

    def __init__(self,
                 xknx,
                 name,
                 group_address,
                 value_type,
                 writable=False,
                 device_updated_cb=None):
        """ Initialize HtHeatpumpParam class. """
        super().__init__(xknx, name, device_updated_cb)

        self.param_value = None
        if value_type == "binary":
            self.param_value = RemoteValueSwitch(
                xknx,
                group_address=group_address,
                device_name=self.name,
                after_update_cb=self.after_update)
        else:
            self.param_value = RemoteValueSensor(
                xknx,
                group_address=group_address,
                device_name=self.name,
                after_update_cb=self.after_update,
                value_type=value_type)
        self.writable = writable

    @classmethod
    def from_config(cls, xknx, name, config):
        """ Initialize object from configuration structure. """
        group_address = config.get("group_address")
        value_type = config.get("value_type")
        writable = config.get("writable")

        return cls(xknx,
                   name,
                   group_address=group_address,
                   value_type=value_type,
                   writable=writable)

    def has_group_address(self, group_address):
        """ Test if device has given group address. """
        return self.param_value.has_group_address(group_address)

    def state_addresses(self):
        """ Return group addresses which should be requested to sync state. """
        return []  # not needed!

    async def process_group_read(self, telegram):
        """ Process incoming GROUP READ telegram. """
        self.xknx.logger.info("HtHeatpumpParam.process_group_read: {!s}".format(telegram))
        # TODO query value, try/except
        value = 123
        #value = ht_heatpump.get_param(self.name)
        self.xknx.logger.info("HtHeatpumpParam.process_group_read: ht_heatpump.get_param({!r}) -> {}".format(
            self.name, value))
        self.param_value.payload = self.param_value.to_knx(value)
        await self.param_value.send(response=True)

    async def process_group_write(self, telegram):
        """ Process incoming GROUP WRITE telegram. """
        self.xknx.logger.info("HtHeatpumpParam.process_group_write: {!s}".format(telegram))
        if await self.param_value.process(telegram):
            value = self.param_value.value
            if not self.writable:
                self.xknx.logger.warning(
                    "Attempted to set value for non-writable heat pump parameter: {!r} (value: {!r})".format(
                        self.name, value))
                return
            # TODO set value, try/except
            self.xknx.logger.info("HtHeatpumpParam.process_group_write: ht_heatpump.set_param({!r}, {})".format(
                self.name, value))
            #value = ht_heatpump.set_param(self.name, value)
            self.param_value.payload = self.param_value.to_knx(value)

    async def set(self, value):
        """ Set new value. """
        await self.param_value.set(value)

    def unit_of_measurement(self):
        """ Return the unit of measurement. """
        return self.param_value.unit_of_measurement

    def resolve_state(self):
        """ Return the current state of the sensor as a human readable string. """
        return self.param_value.value

    def __str__(self):
        """ Return object as readable string. """
        return '<HtHeatpumpParam name="{0}" ' \
               'sensor="{1}" value="{2}" unit="{3}" writable="{4}"/>' \
            .format(self.name,
                    self.param_value.group_addr_str(),
                    self.resolve_state(),
                    self.unit_of_measurement(),
                    "yes" if self.writable else "no")

    def __eq__(self, other):
        """ Equal operator. """
        return self.__dict__ == other.__dict__
