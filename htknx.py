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

import asyncio
import logging
import pprint

from xknx import XKNX
from xknx.devices import Notification
from datetime import timedelta
from htheatpump import HtHeatpump
from typing import Dict, Optional, Type

from config import Config
from htdatapoint import HtDataPoint
from htfaultnotification import HtFaultNotification


_LOGGER = logging.getLogger(__name__)


class HtPublisher:
    """Class for periodically updating and publishing Heliotherm heat pump data points."""

    def __init__(
        self,
        hthp: HtHeatpump,
        data_points: Dict[str, HtDataPoint],
        notifications: Dict[str, Type[Notification]],
        update_interval: timedelta,
        cyclic_sending_interval: timedelta,
    ):
        """Initialize the HtPublisher class."""
        self._hthp = hthp
        self._data_points = data_points
        self._notifications = notifications
        self._update_interval = update_interval
        self._cyclic_sending_interval = cyclic_sending_interval
        self._update_task: Optional[asyncio.Task] = None
        self._cyclic_sending_task: Optional[asyncio.Task] = None

    def __del__(self):
        """Destructor, cleaning up if this was not done before."""
        self.stop()

    def start(self) -> None:
        """Start the HtPublisher."""
        if self._update_task is None:
            self._update_task = self._create_update_task(self._update_interval)
        if self._cyclic_sending_task is None:
            self._cyclic_sending_task = self._create_cyclic_sending_task(
                self._cyclic_sending_interval
            )

    def stop(self) -> None:
        """Stop the HtPublisher."""
        if self._update_task is not None:
            self._update_task.cancel()
            self._update_task = None
        if self._cyclic_sending_task is not None:
            self._cyclic_sending_task.cancel()
            self._cyclic_sending_task = None

    def __enter__(self) -> "HtPublisher":
        """Start the HtPublisher from context manager."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Stop the HtPublisher from context manager."""
        self.stop()

    def _create_update_task(self, update_interval: timedelta) -> Optional[asyncio.Task]:
        """Create an asyncio.Task for updating the heat pump parameter values periodically."""

        async def update_loop(self, update_interval: timedelta):
            """Endless loop for updating the heat pump parameter values."""
            while True:
                _LOGGER.info("*** update ***")  # TODO remove!
                for notif in self._notifications.values():
                    notif.do()
                try:
                    params = await self._hthp.query_async(*self._data_points.keys())
                    for name, value in params.items():
                        await self._data_points[name].set(value)
                except Exception as ex:
                    _LOGGER.exception(ex)
                await asyncio.sleep(update_interval.total_seconds())

        if update_interval.total_seconds() > 0:
            loop = asyncio.get_event_loop()
            return loop.create_task(update_loop(self, update_interval=update_interval))
        return None

    def _create_cyclic_sending_task(
        self, cyclic_sending_interval: timedelta
    ) -> Optional[asyncio.Task]:
        """Create an asyncio.Task for sending the heat pump parameter values periodically to the KNX bus."""

        async def cyclic_sending_loop(self, cyclic_sending_interval: timedelta):
            """Endless loop for sending the heat pump parameter values to the KNX bus."""
            while True:
                _LOGGER.info("*** cyclic_sending ***")  # TODO remove!
                for dp in self._data_points.values():
                    await dp.broadcast_value()
                await asyncio.sleep(cyclic_sending_interval.total_seconds())

        if cyclic_sending_interval.total_seconds() > 0:
            loop = asyncio.get_event_loop()
            return loop.create_task(
                cyclic_sending_loop(
                    self, cyclic_sending_interval=cyclic_sending_interval
                )
            )
        return None


async def main():
    # activate logging with level INFO
    log_format = "%(asctime)s %(levelname)s [%(name)s|%(funcName)s]: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    config = Config()
    config.read("htknx.yaml")
    pprint.pprint(config.__dict__)

    hthp = HtHeatpump(**config.heat_pump)
    xknx = XKNX(**config.knx)

    # create data points
    data_points: Dict[str, HtDataPoint] = {}
    for dp_name, dp_conf in config.data_points.items():
        data_points[dp_name] = HtDataPoint.from_config(xknx, hthp, dp_name, dp_conf)

    # create notifications
    notifications: Dict[str, Type[Notification]] = {}
    for notif_name, notif_conf in config.notifications.items():
        if notif_name == "on_malfunction":
            notifications[notif_name] = HtFaultNotification.from_config(
                xknx, hthp, notif_name, notif_conf
            )

    publisher = HtPublisher(hthp, data_points, notifications, **config.general)

    await xknx.start()
    publisher.start()
    # Wait until Ctrl-C was pressed
    await xknx.loop_until_sigint()
    await xknx.stop()


if __name__ == "__main__":
    asyncio.run(main())
