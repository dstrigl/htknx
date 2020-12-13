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

from xknx import XKNX
from config import Config

_LOGGER = logging.getLogger(__name__)


# TODO HtParamCache (performs the write and the cyclic update; stores the values in a dict)


async def main():
    # activate logging with level DEBUG
    log_format = "%(asctime)s %(levelname)s [%(name)s|%(funcName)s]: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    xknx = XKNX()
    Config(xknx).read("htknx.yaml")

    await xknx.start()
    # Wait until Ctrl-C was pressed
    await xknx.loop_until_sigint()
    await xknx.stop()


if __name__ == "__main__":
    asyncio.run(main())
