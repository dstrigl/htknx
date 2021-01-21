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

""" Heliotherm heat pump KNX gateway main application. """

import argparse
import asyncio
import logging
import logging.config
import os
import sys
import textwrap
from datetime import timedelta
from typing import Dict, Optional, Type

from htheatpump import AioHtHeatpump
from xknx import XKNX
from xknx.devices import Notification

from .__version__ import __version__
from .config import Config
from .htdatapoint import HtDataPoint
from .htfaultnotification import HtFaultNotification

_LOGGER = logging.getLogger(__name__)


DEFAULT_LOGIN_INTERVAL = timedelta(seconds=30)


class HtPublisher:
    """Class for periodically updating and publishing Heliotherm heat pump data points."""

    def __init__(
        self,
        hthp: AioHtHeatpump,
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
        self._login_task: Optional[asyncio.Task] = None
        self._update_task: Optional[asyncio.Task] = None
        self._cyclic_sending_task: Optional[asyncio.Task] = None

    def __del__(self):
        """Destructor, cleaning up if this was not done before."""
        self.stop()

    def start(self) -> None:
        """Start the HtPublisher."""
        if self._login_task is None:
            self._login_task = self._create_login_task(DEFAULT_LOGIN_INTERVAL)
        if self._update_task is None:
            self._update_task = self._create_update_task(self._update_interval)
        if self._cyclic_sending_task is None:
            self._cyclic_sending_task = self._create_cyclic_sending_task(
                self._cyclic_sending_interval
            )

    def stop(self) -> None:
        """Stop the HtPublisher."""
        if self._login_task is not None:
            self._login_task.cancel()
            self._login_task = None
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

    def _create_login_task(self, login_interval: timedelta) -> Optional[asyncio.Task]:
        """Create an asyncio.Task to periodically login to the heat pump."""

        async def login_loop(self, login_interval: timedelta):
            """Endless loop to periodically login to the heat pump."""
            while True:
                _LOGGER.info("<<< [ LOGIN (every %s) ] >>>", login_interval)
                try:
                    await self._hthp.login_async()
                except Exception as ex:
                    _LOGGER.exception(ex)
                # wait until next run
                await asyncio.sleep(login_interval.total_seconds())

        if login_interval.total_seconds() > 0:
            loop = asyncio.get_event_loop()
            return loop.create_task(login_loop(self, login_interval=login_interval))
        return None

    def _create_update_task(self, update_interval: timedelta) -> Optional[asyncio.Task]:
        """Create an asyncio.Task for updating the heat pump parameter values periodically."""

        async def update_loop(self, update_interval: timedelta):
            """Endless loop for updating the heat pump parameter values."""
            while True:
                _LOGGER.info("<<< [ UPDATE (every %s) ] >>>", update_interval)
                # check for notifications
                for notif in self._notifications.values():
                    await notif.do()
                # update the data point values
                try:
                    params = await self._hthp.query_async(*self._data_points.keys())
                    _LOGGER.info("Update: %s", params)
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
                _LOGGER.info(
                    "<<< [ CYCLIC SENDING (every %s) ] >>>", cyclic_sending_interval
                )
                _LOGGER.info(
                    "Sending: %s",
                    [
                        name
                        for name, dp in self._data_points.items()
                        if dp.cyclic_sending
                    ],
                )
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


async def main_async():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """\
            Heliotherm heat pump KNX gateway, v{}.

              https://github.com/dstrigl/htknx
            """.format(
                __version__
            )
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

    # parse the passed arguments
    args = parser.parse_args()
    print(args)

    try:
        # load logging config from file
        logging.config.fileConfig(args.logging_config, disable_existing_loggers=False)
    except Exception as ex:
        _LOGGER.error(
            "Failed to read logging config file '%s': %s", args.config_file, ex
        )
        sys.exit(1)

    try:
        # load the settings from the config file
        config = Config()
        _LOGGER.info("Load settings from '%s'.", args.config_file)
        config.read(args.config_file)
        _LOGGER.debug("Config: %s", config.__dict__)
    except Exception as ex:
        _LOGGER.error(
            "Failed to read gateway config file '%s': %s", args.config_file, ex
        )
        sys.exit(1)

    _LOGGER.info("Start Heliotherm heat pump KNX gateway v%s.", __version__)
    try:
        # create objects to establish connection to the heat pump and the KNX bus
        hthp = AioHtHeatpump(**config.heat_pump)
        xknx = XKNX(**config.knx)

        group_addresses: Dict[str, str] = {}

        # create data points
        data_points: Dict[str, HtDataPoint] = {}
        for dp_name, dp_conf in config.data_points.items():
            data_points[dp_name] = HtDataPoint.from_config(xknx, hthp, dp_name, dp_conf)
            _LOGGER.debug("DP: %s", data_points[dp_name])
            ga = str(data_points[dp_name].group_address)
            if ga in group_addresses:
                raise RuntimeError(
                    "Multiple use of the same KNX group address"
                    f" {ga!r} ({group_addresses[ga]!r} and {dp_name!r})"
                )
            group_addresses[ga] = dp_name

        # create notifications
        notifications: Dict[str, Type[Notification]] = {}
        for notif_name, notif_conf in config.notifications.items():
            if notif_name == "on_malfunction":
                notifications[notif_name] = HtFaultNotification.from_config(
                    xknx, hthp, notif_name, notif_conf
                )
                _LOGGER.debug("NOTIF: %s", notifications[notif_name])
            else:
                _LOGGER.warning("Invalid notification '%s'", notif_name)
                # assert 0, "Invalid notification"
            ga = str(notifications[notif_name].group_address)
            if ga in group_addresses:
                raise RuntimeError(
                    "Multiple use of the same KNX group address"
                    f" {ga!r} ({group_addresses[ga]!r} and {notif_name!r})"
                )
            group_addresses[ga] = notif_name

        # open the connection to the Heliotherm heat pump and login
        hthp.open_connection()
        await hthp.login_async()
        rid = await hthp.get_serial_number_async()
        _LOGGER.info("Connected successfully to heat pump with serial number %d.", rid)
        ver = await hthp.get_version_async()
        _LOGGER.info("Software version = %s (%d)", *ver)

        # start the KNX module which connects to the KNX/IP gateway
        await xknx.start()

        # create and start the publisher
        with HtPublisher(hthp, data_points, notifications, **config.general):
            # Wait until Ctrl-C was pressed
            await xknx.loop_until_sigint()

        # stop the KNX module
        await xknx.stop()

    except Exception as ex:
        _LOGGER.error("Failed to start Heliotherm heat pump KNX gateway: %s", ex)
        sys.exit(1)
    finally:
        await hthp.logout_async()  # try to logout for an ordinary cancellation (if possible)
        hthp.close_connection()

    sys.exit(0)


def main():
    # run the async main application
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
