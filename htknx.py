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

import os
import asyncio
import logging
import logging.config
import pprint
import argparse
import textwrap

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
                _LOGGER.info("*** UPDATE run ***")
                # check for notifications
                for notif in self._notifications.values():
                    await notif.do()
                # update the data point values
                try:
                    params = await self._hthp.query_async(*self._data_points.keys())
                    _LOGGER.debug("%s", params)
                    for name, value in params.items():
                        await self._data_points[name].set(value)
                except Exception as ex:
                    _LOGGER.exception(ex)
                # wait until next run
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
                _LOGGER.info("*** CYCLIC SENDING run ***")
                # broadcast the data point values to the KNX bus
                for dp in self._data_points.values():
                    await dp.broadcast_value()
                # wait until next run
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
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """\
            Heliotherm heat pump KNX gateway
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            DISCLAIMER
            ----------
              Please note that any incorrect or careless usage of this program as well as
              errors in the implementation can damage your heat pump!
              Therefore, the author does not provide any guarantee or warranty concerning
              to correctness, functionality or performance and does not accept any liability
              for damage caused by this program or mentioned information.
              Thus, use it on your own risk!
            """
        )
        + "\r\n",
    )

    parser.add_argument(
        "config_file",
        default=os.path.normpath(os.path.join(os.path.dirname(__file__), "htknx.yaml")),
        type=str,
        nargs="?",
        help="the filename under which the gateway settings can be found, default: %(default)s",
    )

    parser.add_argument(
        "--logging-config",
        default=os.path.normpath(
            os.path.join(os.path.dirname(__file__), "logging.conf")
        ),
        type=str,
        help="the filename under which the logging configuration can be found, default: %(default)s",
    )

    args = parser.parse_args()
    print(args)

    # load logging config from file
    logging.config.fileConfig(args.logging_config, disable_existing_loggers=False)

    _LOGGER.info(
        "Start Heliotherm heat pump KNX gateway v%s.", "0.1"  # __version__
    )  # TODO __version__

    config = Config()
    _LOGGER.info("Load settings from '%s'.", args.config_file)
    config.read(args.config_file)
    _LOGGER.debug("config: %s", config.__dict__)

    hthp = HtHeatpump(**config.heat_pump)
    hthp.open_connection()
    await hthp.login_async()
    rid = await hthp.get_serial_number_async()
    _LOGGER.info("connected successfully to heat pump with serial number %d", rid)
    ver = await hthp.get_version_async()
    _LOGGER.info("software version = %s (%d)", *ver)

    xknx = XKNX(**config.knx)

    # create data points
    data_points: Dict[str, HtDataPoint] = {}
    for dp_name, dp_conf in config.data_points.items():
        data_points[dp_name] = HtDataPoint.from_config(xknx, hthp, dp_name, dp_conf)
        _LOGGER.debug("data point: %s", data_points[dp_name])

    # create notifications
    notifications: Dict[str, Type[Notification]] = {}
    for notif_name, notif_conf in config.notifications.items():
        if notif_name == "on_malfunction":
            notifications[notif_name] = HtFaultNotification.from_config(
                xknx, hthp, notif_name, notif_conf
            )
            _LOGGER.debug("notification: %s", notifications[notif_name])
        else:
            _LOGGER.error("invalid notification '%s'", notif_name)
            assert 0, "invalid notification"

    await xknx.start()

    publisher = HtPublisher(hthp, data_points, notifications, **config.general)
    publisher.start()

    # Wait until Ctrl-C was pressed
    await xknx.loop_until_sigint()

    publisher.stop()
    await xknx.stop()

    await hthp.logout_async()  # try to logout for an ordinary cancellation (if possible)
    hthp.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
