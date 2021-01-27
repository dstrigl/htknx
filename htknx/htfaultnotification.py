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

""" Notification to inform about malfunctioning of the Heliotherm heat pump. """

import logging
from datetime import datetime, timedelta
from typing import Optional

from htheatpump import AioHtHeatpump
from xknx import XKNX
from xknx.devices import Notification
from xknx.telegram import GroupAddress, TelegramDirection

_LOGGER = logging.getLogger(__name__)


class HtFaultNotification(Notification):
    """Representation of a Heliotherm fault message notification."""

    def __init__(
        self,
        xknx: XKNX,
        hthp: AioHtHeatpump,
        name: str,
        group_address,
        repeat_after: Optional[timedelta],
        device_updated_cb=None,
    ):
        """Initialize HtFaultNotification class."""
        super().__init__(xknx, name, group_address, device_updated_cb)
        self.hthp = hthp
        self.repeat_after = repeat_after
        self.last_sent_at = None
        self.in_error = False

    @classmethod
    def from_config(cls, xknx, hthp, name, config, device_updated_cb=None):
        """Initialize object from configuration structure."""
        group_address = config.get("group_address")
        repeat_after = config.get("repeat_after")

        return cls(
            xknx, hthp, name, group_address=group_address, repeat_after=repeat_after
        )

    @property
    def group_address(self) -> GroupAddress:
        return self._message.group_address

    async def process_group_read(self, telegram):
        """Process incoming GROUP READ telegram."""
        if telegram.direction == TelegramDirection.OUTGOING:
            return
        _LOGGER.info(
            "Received GROUP READ telegram for notification '%s' [%s]: %s",
            self.name,
            self.group_address,
            telegram,
        )
        try:
            # query for the last fault message of the heat pump
            idx, err, dt, msg = await self.hthp.get_last_fault_async()
            _LOGGER.info("ERROR #%s [%s]: %s, %s", idx, dt.isoformat(), err, msg)
            # and send it as notification on the KNX bus
            await self.set(msg)
        except Exception as ex:
            _LOGGER.exception(ex)

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if telegram.direction == TelegramDirection.OUTGOING:
            return
        _LOGGER.warning(
            "Ignored received GROUP WRITE telegram for notification '%s' [%s]: %s",
            self.name,
            self.group_address,
            telegram,
        )

    async def do(self):
        """Execute the 'do' command."""
        try:
            # query whether the heat pump is malfunctioning
            if await self.hthp.in_error_async:
                if not self.in_error or (
                    self.repeat_after is not None
                    and datetime.now() - self.last_sent_at >= self.repeat_after
                ):
                    _LOGGER.info(
                        "HEAT PUMP in ERROR%s", " (repeated)" if self.in_error else ""
                    )
                    # query for the last fault message of the heat pump
                    idx, err, dt, msg = await self.hthp.get_last_fault_async()
                    _LOGGER.info(
                        "ERROR #%s [%s]: %s, %s", idx, dt.isoformat(), err, msg
                    )
                    # and send it as notification on the KNX bus
                    await self.set(msg)

                    self.in_error = True
                    self.last_sent_at = datetime.now()
            else:
                self.in_error = False
        except Exception as ex:
            _LOGGER.exception(ex)

    def __str__(self):
        """Return object as readable string."""
        return (
            '<HtFaultNotification name="{}" group_address="{}"'
            ' repeat_after="{}" last_sent_at="{}" in_error="{}"/>'
        ).format(
            self.name,
            self.group_address,
            self.repeat_after,
            self.last_sent_at,
            self.in_error,
        )
