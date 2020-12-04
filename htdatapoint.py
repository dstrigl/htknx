#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" TODO """

from xknx.devices import Device
from xknx.remote_value.remote_value_sensor import RemoteValueSensor
from xknx.remote_value.remote_value_switch import RemoteValueSwitch

# from ??? import ht_heatpump  # type: ignore

# import logging
# _logger = logging.getLogger(__name__)


class HtDataPoint(Device):
    """ Representation of a Heliotherm heat pump parameter. """

    def __init__(
        self,
        xknx,
        name: str,
        group_address,
        value_type: str,
        writable: bool = False,
    ):
        """ Initialize HtHeatpumpParam class. """
        super().__init__(xknx, name)

        self.param_value = None
        if value_type == "binary":
            self.param_value = RemoteValueSwitch(
                xknx,
                group_address=group_address,
                sync_state=False,
                device_name=self.name,
                after_update_cb=self.after_update,
            )
        else:
            self.param_value = RemoteValueSensor(
                xknx,
                group_address=group_address,
                sync_state=False,
                device_name=self.name,
                after_update_cb=self.after_update,
                value_type=value_type,
            )
        self.writable = writable

    def _iter_remote_values(self):
        """ Iterate the devices RemoteValue classes. """
        yield self.param_value

    @classmethod
    def from_config(cls, xknx, name, config):
        """ Initialize object from configuration structure. """
        group_address = config.get("group_address")
        value_type = config.get("value_type")
        writable = config.get("writable")

        return cls(
            xknx,
            name,
            group_address=group_address,
            value_type=value_type,
            writable=writable,
        )

    async def broadcast_value(self, response=False):
        """ Broadcast parameter value to KNX bus. """
        # TODO query value, try/except
        value = 123
        # value = await ht_heatpump.get_param_async(self.name)
        self.xknx.logger.info(
            "HtHeatpumpParam.broadcast_value: ht_heatpump.get_param('%s') -> %s",
            self.name,
            value,
        )
        await self.param_value.set(value, response=response)

    async def process_group_read(self, telegram):
        """ Process incoming GROUP READ telegram. """
        self.xknx.logger.info("HtHeatpumpParam.process_group_read: %s", telegram)
        await self.broadcast_value(True)

    async def process_group_write(self, telegram):
        """ Process incoming GROUP WRITE telegram. """
        self.xknx.logger.info("HtHeatpumpParam.process_group_write: %s", telegram)
        if await self.param_value.process(telegram):
            value = self.param_value.value
            if not self.writable:
                self.xknx.logger.warning(
                    "Attempted to set value for non-writable heat pump parameter: '%s' (value: %s)",
                    self.name,
                    value,
                )
                return
            # TODO set value, try/except
            self.xknx.logger.info(
                "HtHeatpumpParam.process_group_write: ht_heatpump.set_param('%s', %s)",
                self.name,
                value,
            )
            # value = await ht_heatpump.set_param_async(self.name, value)
            self.param_value.payload = self.param_value.to_knx(value)

    def unit_of_measurement(self):
        """ Return the unit of measurement. """
        return self.param_value.unit_of_measurement

    def resolve_state(self):
        """ Return the current state of the heat pump parameter as a human readable string. """
        return self.param_value.value

    def __str__(self):
        """ Return object as readable string. """
        return '<HtDataPoint name="{}" group-address="{}" value_type="{}" value="{}" unit="{}" writable="{}"/>'.format(
            self.name,
            self.param_value.group_address,
            "binary"
            if isinstance(self.param_value, RemoteValueSwitch)
            else self.param_value.dpt_class.value_type,
            self.resolve_state(),
            self.unit_of_measurement(),
            "yes" if self.writable else "no",
        )
