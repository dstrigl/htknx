#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" TODO """

import logging

from xknx import XKNX
from xknx.devices import Notification
from htheatpump import HtHeatpump
from datetime import timedelta, datetime
from typing import Optional


_LOGGER = logging.getLogger(__name__)


class HtFaultNotification(Notification):
    """Representation of a Heliotherm fault message notification."""

    def __init__(
        self,
        xknx: XKNX,
        hthp: HtHeatpump,
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

    async def do(self):
        """Execute the 'do' command."""
        try:
            # query whether the heat pump is malfunctioning
            # if await self.hthp.in_error_async:
            if (
                await self.hthp.get_param_async("Zirkulationspumpe WW") == True
            ):  # TODO remove!
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
            self._message.group_address,
            self.repeat_after,
            self.last_sent_at,
            self.in_error,
        )
