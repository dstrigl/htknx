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

""" Representation of a Heliotherm heat pump parameter as a data point. """

import logging
from typing import Union

from htheatpump import AioHtHeatpump, HtDataTypes, HtParams
from xknx import XKNX
from xknx.devices import Device
from xknx.remote_value.remote_value_sensor import RemoteValueSensor
from xknx.remote_value.remote_value_switch import RemoteValueSwitch
from xknx.telegram import GroupAddress, TelegramDirection

_LOGGER = logging.getLogger(__name__)


class HtDataPoint(Device):
    """Representation of a Heliotherm heat pump data point."""

    def __init__(
        self,
        xknx: XKNX,
        hthp: AioHtHeatpump,
        name: str,
        group_address,
        value_type: str,
        writable: bool = False,
        cyclic_sending: bool = False,
        send_on_change: bool = False,
        on_change_of_absolute: Union[None, int, float] = None,
        on_change_of_relative: Union[None, int, float] = None,
        device_updated_cb=None,
    ):
        """Initialize HtDataPoint class."""
        super().__init__(xknx, name, device_updated_cb)
        self.hthp = hthp

        if value_type == "binary":
            assert on_change_of_absolute is None and on_change_of_relative is None
            self.param_value = RemoteValueSwitch(
                xknx,
                group_address=group_address,
                sync_state=False,
                device_name=self.name,
                after_update_cb=self.after_update,
            )
        else:
            assert not (
                on_change_of_absolute is not None and on_change_of_relative is not None
            )
            assert (
                not send_on_change
                or on_change_of_absolute is not None
                or on_change_of_relative is not None
            )
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
        self.on_change_of_absolute = on_change_of_absolute
        self.on_change_of_relative = on_change_of_relative
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
        on_change_of_absolute = config.get("on_change_of_absolute")
        on_change_of_relative = config.get("on_change_of_relative")

        return cls(
            xknx,
            hthp,
            name,
            group_address=group_address,
            value_type=value_type,
            writable=writable,
            cyclic_sending=cyclic_sending,
            send_on_change=send_on_change,
            on_change_of_absolute=on_change_of_absolute,
            on_change_of_relative=on_change_of_relative,
            device_updated_cb=device_updated_cb,
        )

    @property
    def group_address(self) -> GroupAddress:
        return self.param_value.group_address

    async def broadcast_value(self, response=False):
        """Broadcast parameter value to KNX bus."""
        if response or self.cyclic_sending:
            value = self.param_value.value
            if value is None:
                return
            _LOGGER.debug(
                "Broadcast DP '%s' [%s]: value=%s (response: %s, cyclic_sending: %s)",
                self.name,
                self.param_value.group_address,
                value,
                response,
                self.cyclic_sending,
            )
            await self.param_value.set(value, response=response)
            # if response:  # TODO necessary?
            #     self.last_sent_value = value

    async def process_group_read(self, telegram):
        """Process incoming GROUP READ telegram."""
        if telegram.direction == TelegramDirection.OUTGOING:
            return
        _LOGGER.info(
            "Received GROUP READ telegram for DP '%s' [%s]: %s",
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
            "Received GROUP WRITE telegram for DP '%s' [%s]: %s",
            self.name,
            self.param_value.group_address,
            telegram,
        )
        if await self.param_value.process(telegram):
            value = self.param_value.value
            if not self.writable:
                _LOGGER.warning(
                    "Attempted to set value for non-writable heat pump DP '%s' [%s] (value: %s).",
                    self.name,
                    self.param_value.group_address,
                    value,
                )
                return
            try:
                param = HtParams[self.name]
                if param.data_type == HtDataTypes.INT:
                    value = int(value)
                elif param.data_type == HtDataTypes.FLOAT:
                    value = float(value)
                elif param.data_type == HtDataTypes.BOOL:
                    value = bool(value)
                else:
                    assert 0, f"Invalid dp_type ({param.data_type})"
                value = await self.hthp.set_param_async(self.name, value)
                self.param_value.payload = self.param_value.to_knx(value)
            except Exception as ex:
                _LOGGER.exception(ex)

    async def set(self, value):
        """Set new value and send it to the KNX bus if desired."""

        def numeric_value_changed(value) -> bool:
            """Determines whether a numeric value changed or not."""
            assert self.last_sent_value is not None
            if self.on_change_of_absolute is not None:
                return abs(value - self.last_sent_value) >= abs(
                    self.on_change_of_absolute
                )
            elif self.on_change_of_relative is not None:
                if self.last_sent_value == 0 and value != 0:
                    return True
                elif self.last_sent_value == 0:
                    return False
                else:
                    return (
                        abs(value - self.last_sent_value) / self.last_sent_value
                    ) * 100 >= abs(self.on_change_of_relative)
            assert 0, "must contain on_change_of_absolute or on_change_of_relative"
            return False

        if value is None:
            return

        # binary value type
        if isinstance(self.param_value, RemoteValueSwitch):
            if self.send_on_change and (
                self.last_sent_value is None or value != self.last_sent_value
            ):
                _LOGGER.debug(
                    "Update and send DP '%s' [%s]: value=%s (send_on_change: %s, last_sent_value: %s)",
                    self.name,
                    self.param_value.group_address,
                    value,
                    self.send_on_change,
                    self.last_sent_value,
                )
                await self.param_value.set(value)
                self.last_sent_value = value
            else:
                _LOGGER.debug(
                    "Update DP '%s' [%s]: value=%s (send_on_change: %s, last_sent_value: %s)",
                    self.name,
                    self.param_value.group_address,
                    value,
                    self.send_on_change,
                    self.last_sent_value,
                )
                self.param_value.payload = self.param_value.to_knx(value)
        # numeric value type
        elif isinstance(self.param_value, RemoteValueSensor):
            if self.send_on_change and (
                self.last_sent_value is None or numeric_value_changed(value)
            ):
                _LOGGER.info(
                    "Update and send DP '%s' [%s]: value=%s (send_on_change: %s,"
                    " on_change_of_absolute: %s, on_change_of_relative: %s, last_sent_value: %s)",
                    self.name,
                    self.param_value.group_address,
                    value,
                    self.send_on_change,
                    self.on_change_of_absolute,
                    self.on_change_of_relative,
                    self.last_sent_value,
                )
                await self.param_value.set(value)
                self.last_sent_value = value
            else:
                _LOGGER.debug(
                    "Update DP '%s' [%s]: value=%s (send_on_change: %s,"
                    " on_change_of_absolute: %s, on_change_of_relative: %s, last_sent_value: %s)",
                    self.name,
                    self.param_value.group_address,
                    value,
                    self.send_on_change,
                    self.on_change_of_absolute,
                    self.on_change_of_relative,
                    self.last_sent_value,
                )
                self.param_value.payload = self.param_value.to_knx(value)
        # invalid value type
        else:
            assert 0, "Invalid param_value type"

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
            ' writable="{}" cyclic_sending="{}" send_on_change="{}"'
            ' on_change_of_absolute="{}" on_change_of_relative="{}" last_sent_value="{}"/>'
        ).format(
            self.name,
            self.group_address,
            "binary"
            if isinstance(self.param_value, RemoteValueSwitch)
            else self.param_value.dpt_class.value_type,
            self.resolve_state(),
            self.unit_of_measurement(),
            "yes" if self.writable else "no",
            "yes" if self.cyclic_sending else "no",
            "yes" if self.send_on_change else "no",
            self.on_change_of_absolute,
            self.on_change_of_relative,
            self.last_sent_value,
        )
