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

""" Helpers for config validation using voluptuous. """

from datetime import timedelta
from numbers import Number
from typing import Any, Callable, Dict, List, TypeVar, Union

import voluptuous as vol
from xknx.dpt import DPTBase
from xknx.telegram import GroupAddress, IndividualAddress

# typing typevar
T = TypeVar("T")


port = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


# Adapted from:
# https://github.com/alecthomas/voluptuous/issues/115#issuecomment-144464666
#
def has_at_least_one_key(*keys: str) -> Callable:
    """Validate that at least one key exists."""

    def validate(obj: Dict) -> Dict:
        """Test keys exist in dict."""
        if not isinstance(obj, dict):
            raise vol.Invalid("expected dictionary")

        for k in obj:
            if k in keys:
                return obj
        raise vol.Invalid("must contain at least one of {}".format(", ".join(keys)))

    return validate


time_period_dict = vol.All(
    dict,
    vol.Schema(
        {
            "days": vol.Coerce(float),
            "hours": vol.Coerce(float),
            "minutes": vol.Coerce(float),
            "seconds": vol.Coerce(float),
            "milliseconds": vol.Coerce(float),
        }
    ),
    has_at_least_one_key("days", "hours", "minutes", "seconds", "milliseconds"),
    lambda value: timedelta(**value),
)


TIME_PERIOD_ERROR = "offset {} should be format 'HH:MM', 'HH:MM:SS' or 'HH:MM:SS.F'"


def time_period_str(value: str) -> timedelta:
    """Validate and transform time offset."""
    if isinstance(value, int):  # type: ignore
        raise vol.Invalid("make sure you wrap time values in quotes")
    if not isinstance(value, str):
        raise vol.Invalid(TIME_PERIOD_ERROR.format(value))

    negative_offset = False
    if value.startswith("-"):
        negative_offset = True
        value = value[1:]
    elif value.startswith("+"):
        value = value[1:]

    parsed = value.split(":")
    if len(parsed) not in (2, 3):
        raise vol.Invalid(TIME_PERIOD_ERROR.format(value))
    try:
        hour = int(parsed[0])
        minute = int(parsed[1])
        try:
            second = float(parsed[2])
        except IndexError:
            second = 0
    except ValueError as err:
        raise vol.Invalid(TIME_PERIOD_ERROR.format(value)) from err

    offset = timedelta(hours=hour, minutes=minute, seconds=second)

    if negative_offset:
        offset *= -1

    return offset


def time_period_seconds(value: Union[float, str]) -> timedelta:
    """Validate and transform seconds to a time offset."""
    try:
        return timedelta(seconds=float(value))
    except (ValueError, TypeError) as err:
        raise vol.Invalid(f"expected seconds, got {value!r}") from err


time_period = vol.Any(time_period_str, time_period_seconds, timedelta, time_period_dict)


def positive_timedelta(value: timedelta) -> timedelta:
    """Validate timedelta is positive."""
    if value < timedelta(0):
        raise vol.Invalid("time period should be positive")
    return value


def timedelta_greater_zero(value: timedelta) -> timedelta:
    """Validate timedelta is greater zero (0)."""
    if value <= timedelta(0):
        raise vol.Invalid("time period should be greater zero")
    return value


# time_interval = vol.All(time_period, positive_timedelta)
time_interval = vol.All(time_period, timedelta_greater_zero)


def string(value: Any) -> str:
    """Coerce value to string, except for None."""
    if value is None:
        raise vol.Invalid("string value is None")

    if isinstance(value, (list, dict)):
        raise vol.Invalid("value should be a string")

    return str(value)


def boolean(value: Any) -> bool:
    """Validate and coerce a boolean value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower().strip()
        if value in ("1", "true", "yes", "on", "enable"):
            return True
        if value in ("0", "false", "no", "off", "disable"):
            return False
    elif isinstance(value, Number):
        # type ignore: https://github.com/python/mypy/issues/3186
        return value != 0  # type: ignore
    raise vol.Invalid(f"invalid boolean value {value!r}")


def number(value: Any) -> Union[int, float]:
    """Validate numeric value."""
    if type(value) in (int, float):
        return value
    raise vol.Invalid(f"invalid numeric value {value!r}")


number_greater_zero = vol.All(number, vol.Range(min=0, min_included=False))


def ensure_list(value: Union[T, List[T], None]) -> List[T]:
    """Wrap value in list if it is not one."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def ensure_group_address(value: str) -> str:
    """Ensure value is a valid KNX group address."""
    value = str(value)
    if value.isdigit() and 0 <= int(value) <= GroupAddress.MAX_FREE:
        return value

    if not GroupAddress.ADDRESS_RE.match(value):
        raise vol.Invalid(f"{value!r} is not a valid group address")

    return value


def ensure_individual_address(value: str) -> str:
    """Ensure value is a valid individual address."""
    value = str(value)
    if not IndividualAddress.ADDRESS_RE.match(value):
        raise vol.Invalid(f"{value!r} is not a valid individual address")

    return value


def ensure_knx_dpt(value: str) -> str:
    """Ensure value is a valid KNX DPT."""
    dpt_class = DPTBase.parse_transcoder(value)
    if dpt_class is None:
        raise vol.Invalid(f"{value!r} is not a valid KNX DPT")

    return value
