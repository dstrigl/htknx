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
from datetime import timedelta

from config import Config

_LOGGER = logging.getLogger(__name__)


# TODO HtParamCache (performs the write and the cyclic update; stores the values in a dict)


class HtParamCache:
    """TODO"""

    def __init__(self, config: Config):
        """Initialize the HtParamCache class."""
        self._update_task = self._create_update_task(config.update_interval)
        self._publish_task = self._create_publish_task(config.publish_interval)
        self._data_points = config.data_points
        self._notifications = config.notifications

    def __del__(self):
        """Destructor. Cleaning up if this was not done before."""
        if self._update_task:
            self._update_task.cancel()
        if self._publish_task:
            self._publish_task.cancel()

    def _create_update_task(self, update_interval: timedelta):
        """Create an asyncio.Task for updating the heat pump parameter values periodically."""

        async def update_loop(self, update_interval: timedelta):
            """Endless loop for updating the heat pump parameter values."""
            while True:
                # TODO
                _LOGGER.info("update")
                await asyncio.sleep(update_interval.total_seconds())

        if update_interval.total_seconds() > 0:
            loop = asyncio.get_event_loop()
            return loop.create_task(update_loop(self, update_interval=update_interval))
        return None

    def _create_publish_task(self, publish_interval: timedelta):
        """Create an asyncio.Task for publishing the heat pump parameter values periodically."""

        async def publish_loop(self, publish_interval: timedelta):
            """Endless loop for publishing the heat pump parameter values."""
            while True:
                # TODO
                _LOGGER.info("publish")
                await asyncio.sleep(publish_interval.total_seconds())

        if publish_interval.total_seconds() > 0:
            loop = asyncio.get_event_loop()
            return loop.create_task(
                publish_loop(self, publish_interval=publish_interval)
            )
        return None


async def main():
    # activate logging with level DEBUG
    log_format = "%(asctime)s %(levelname)s [%(name)s|%(funcName)s]: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    xknx = XKNX()
    config = Config(xknx)
    config.read("htknx.yaml")
    pprint.pprint(config.__dict__)

    param_cache = HtParamCache(config)

    await xknx.start()
    # Wait until Ctrl-C was pressed
    await xknx.loop_until_sigint()
    await xknx.stop()


if __name__ == "__main__":
    asyncio.run(main())
