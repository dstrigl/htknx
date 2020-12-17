#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" TODO """

import logging

from xknx import XKNX
from xknx.devices import Device
from xknx.remote_value.remote_value_sensor import RemoteValueSensor
from xknx.remote_value.remote_value_switch import RemoteValueSwitch
from xknx.telegram import TelegramDirection
from htheatpump import HtHeatpump
from typing import Union


_LOGGER = logging.getLogger(__name__)


class HtDataPoint(Device):
    """Representation of a Heliotherm heat pump data point."""

    def __init__(
        self,
        xknx: XKNX,
        hthp: HtHeatpump,
        name: str,
        group_address,
        value_type: str,
        writable: bool = False,
        cyclic_sending: bool = False,
        send_on_change: bool = False,
        on_change_of: Union[None, int, float] = None,
        device_updated_cb=None,
    ):
        """Initialize HtDataPoint class."""
        super().__init__(xknx, name, device_updated_cb)
        self.hthp = hthp

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
        self.cyclic_sending = cyclic_sending
        self.send_on_change = send_on_change
        self.on_change_of = on_change_of
        self.last_sent_value: Union[None, bool, int, float] = None

    def _iter_remote_values(self):
        """Iterate the devices RemoteValue classes."""
        yield self.param_value

    @classmethod
    def from_config(cls, xknx, hthp, name, config, device_updated_cb=None):
        """Initialize object from configuration structure."""
        group_address = config.get("group_address")
        value_type = config.get("value_type")
        writable = config.get("writable")
        cyclic_sending = config.get("cyclic_sending")
        send_on_change = config.get("send_on_change")
        on_change_of = config.get("on_change_of")

        return cls(
            xknx,
            hthp,
            name,
            group_address=group_address,
            value_type=value_type,
            writable=writable,
            cyclic_sending=cyclic_sending,
            send_on_change=send_on_change,
            on_change_of=on_change_of,
            device_updated_cb=device_updated_cb,
        )

    async def broadcast_value(self, response=False):
        """Broadcast parameter value to KNX bus."""
        if response or self.cyclic_sending:
            value = self.param_value.value
            _LOGGER.debug(
                "broadcast DP '%s' (%s): value=%s (response: %s, cyclic_sending: %s)",
                self.name,
                self.param_value.group_address,
                value,
                response,
                self.cyclic_sending,
            )
            if value is None:
                return
            await self.param_value.set(value, response=response)
            # if response:  # TODO necessary?
            #     self.last_sent_value = value

    async def process_group_read(self, telegram):
        """Process incoming GROUP READ telegram."""
        if telegram.direction == TelegramDirection.OUTGOING:
            return
        _LOGGER.info(
            "received GROUP READ telegram for DP '%s' (%s): %s",
            self.name,
            self.param_value.group_address,
            telegram,
        )
        await self.broadcast_value(True)

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if telegram.direction == TelegramDirection.OUTGOING:
            return
        _LOGGER.info(
            "received GROUP WRITE telegram for DP '%s' (%s): %s",
            self.name,
            self.param_value.group_address,
            telegram,
        )
        if await self.param_value.process(telegram):
            value = self.param_value.value
            if not self.writable:
                _LOGGER.warning(
                    "attempted to set value for non-writable heat pump DP '%s' (value: %s)",
                    self.name,
                    value,
                )
                return
            try:
                value = await self.hthp.set_param_async(self.name, value)
                self.param_value.payload = self.param_value.to_knx(value)
            except Exception as ex:
                _LOGGER.exception(ex)

    async def set(self, value):
        """Set new value and send it to the KNX bus if desired."""
        if value is None:
            return
        if isinstance(self.param_value, RemoteValueSwitch):
            _LOGGER.debug(
                "set DP '%s' (%s): value=%s (send_on_change: %s, last_sent_value: %s)",
                self.name,
                self.param_value.group_address,
                value,
                self.send_on_change,
                self.last_sent_value,
            )
            if self.send_on_change:
                await self.param_value.set(value)
                self.last_sent_value = value
            else:
                self.param_value.payload = self.param_value.to_knx(value)
        elif isinstance(self.param_value, RemoteValueSensor):
            _LOGGER.debug(
                "set DP '%s' (%s): value=%s (send_on_change: %s, on_change_of: %s, last_sent_value: %s)",
                self.name,
                self.param_value.group_address,
                value,
                self.send_on_change,
                self.on_change_of,
                self.last_sent_value,
            )
            # TODO on_change_of_relative / on_change_of_absolute
            if self.send_on_change and (
                self.on_change_of is None
                or self.last_sent_value is None
                or abs(value - self.last_sent_value) >= abs(self.on_change_of)
            ):
                await self.param_value.set(value)
                self.last_sent_value = value
            else:
                self.param_value.payload = self.param_value.to_knx(value)
        else:
            assert 0, "invalid param_value type"

    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.param_value.unit_of_measurement

    def resolve_state(self):
        """Return the current state of the heat pump parameter as a human readable string."""
        return self.param_value.value

    def __str__(self):
        """Return object as readable string."""
        return (
            '<HtDataPoint name="{}" group_address="{}" value_type="{}" value="{}" unit="{}"'
            ' writable="{}" cyclic_sending="{}" send_on_change="{}" on_change_of="{}" last_sent_value="{}"/>'
        ).format(
            self.name,
            self.param_value.group_address,
            "binary"
            if isinstance(self.param_value, RemoteValueSwitch)
            else self.param_value.dpt_class.value_type,
            self.resolve_state(),
            self.unit_of_measurement(),
            "yes" if self.writable else "no",
            "yes" if self.cyclic_sending else "no",
            "yes" if self.send_on_change else "no",
            self.on_change_of,
            self.last_sent_value,
        )
