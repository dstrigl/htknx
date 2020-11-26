#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Helpers for config validation using voluptuous. """

from datetime import timedelta
from typing import Any, Union, Callable, Dict
from numbers import Number
import voluptuous as vol
import re


port = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


# Adapted from:
# https://github.com/alecthomas/voluptuous/issues/115#issuecomment-144464666
def has_at_least_one_key(*keys: str) -> Callable:
    """ Validate that at least one key exists. """

    def validate(obj: Dict) -> Dict:
        """ Test keys exist in dict. """
        if not isinstance(obj, dict):
            raise vol.Invalid("expected dictionary")

        for k in obj:
            if k in keys:
                return obj
        raise vol.Invalid("must contain at least one of {}.".format(", ".join(keys)))

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
    """ Validate and transform time offset. """
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
    """ Validate and transform seconds to a time offset. """
    try:
        return timedelta(seconds=float(value))
    except (ValueError, TypeError) as err:
        raise vol.Invalid(f"expected seconds, got {value}") from err


time_period = vol.Any(time_period_str, time_period_seconds, timedelta, time_period_dict)


def positive_timedelta(value: timedelta) -> timedelta:
    """ Validate timedelta is positive. """
    if value < timedelta(0):
        raise vol.Invalid("time period should be positive")
    return value


time_interval = vol.All(time_period, positive_timedelta)


def string(value: Any) -> str:
    """ Coerce value to string, except for None. """
    if value is None:
        raise vol.Invalid("string value is None")

    if isinstance(value, (list, dict)):
        raise vol.Invalid("value should be a string")

    return str(value)


def matches_regex(regex: str) -> Callable[[Any], str]:
    """ Validate that the value is a string that matches a regex. """
    compiled = re.compile(regex)

    def validator(value: Any) -> str:
        """ Validate that value matches the given regex. """
        if not isinstance(value, str):
            raise vol.Invalid(f"not a string value: {value}")

        if not compiled.match(value):
            raise vol.Invalid(
                f"value {value} does not match regular expression {compiled.pattern}"
            )

        return value

    return validator


def boolean(value: Any) -> bool:
    """ Validate and coerce a boolean value. """
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
    raise vol.Invalid(f"invalid boolean value {value}")


def number(value: Any) -> Union[int, float]:
    """ Validate numeric value. """
    if type(value) in (int, float):
        return value
    raise vol.Invalid(f"invalid numeric value {value}")
