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

        for k in obj.keys():
            if k in keys:
                return obj
        raise vol.Invalid("must contain one of {!r}.".format(", ".join(keys)))

    return validate


time_period_dict = vol.All(
    dict, vol.Schema({
        "days": vol.Coerce(int),
        "hours": vol.Coerce(int),
        "minutes": vol.Coerce(int),
        "seconds": vol.Coerce(int),
        "milliseconds": vol.Coerce(int),
    }),
    has_at_least_one_key("days", "hours", "minutes", "seconds", "milliseconds"), lambda value: timedelta(**value))


TIME_PERIOD_ERROR = "offset {!r} should be format 'HH:MM' or 'HH:MM:SS'"


def time_period_str(value: str) -> timedelta:
    """ Validate and transform time offset. """
    if isinstance(value, int):
        raise vol.Invalid("Make sure you wrap time values in quotes")
    if not isinstance(value, str):
        raise vol.Invalid(TIME_PERIOD_ERROR.format(value))

    negative_offset = False
    if value.startswith('-'):
        negative_offset = True
        value = value[1:]
    elif value.startswith('+'):
        value = value[1:]

    try:
        parsed = [int(x) for x in value.split(':')]
    except ValueError:
        raise vol.Invalid(TIME_PERIOD_ERROR.format(value))

    if len(parsed) == 2:
        hour, minute = parsed
        second = 0
    elif len(parsed) == 3:
        hour, minute, second = parsed
    else:
        raise vol.Invalid(TIME_PERIOD_ERROR.format(value))

    offset = timedelta(hours=hour, minutes=minute, seconds=second)

    if negative_offset:
        offset *= -1

    return offset


def time_period_seconds(value: Union[int, str]) -> timedelta:
    """ Validate and transform seconds to a time offset. """
    try:
        return timedelta(seconds=int(value))
    except (ValueError, TypeError):
        raise vol.Invalid("expected seconds, got {!r}".format(value))


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


def matches_regex(regex):
    """ Validate that the value is a string that matches a regex. """
    regex = re.compile(regex)

    def validator(value: Any) -> str:
        """ Validate that value matches the given regex. """
        if not isinstance(value, str):
            raise vol.Invalid("not a string value {!r}".format(value))

        if not regex.match(value):
            raise vol.Invalid("value {!r} does not match regular expression {!r}"
                              .format(value, regex.pattern))

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
        return value != 0
    raise vol.Invalid("invalid boolean value {!r}".format(value))
