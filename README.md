# htknx

[![PyPI version](https://img.shields.io/pypi/v/htknx.svg)](https://pypi.org/project/htknx)
[![Python versions](https://img.shields.io/pypi/pyversions/htknx.svg)](https://pypi.org/project/htknx)
[![License](https://img.shields.io/pypi/l/htknx.svg)](https://pypi.org/project/htknx)
[![Build status](https://github.com/dstrigl/HtREST/workflows/CI/badge.svg)](https://github.com/dstrigl/htknx/actions?query=workflow%3ACI)
[![Updates](https://pyup.io/repos/github/dstrigl/htknx/shield.svg)](https://pyup.io/repos/github/dstrigl/htknx)


[Heliotherm](http://www.heliotherm.com/) heat pump KNX gateway for Python 3.7 and 3.8.

* GitHub repo: https://github.com/dstrigl/htknx
* Free software: [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html)


> **Warning:**
>
> Please note that any incorrect or careless usage of this application as well as
> errors in the implementation can damage your heat pump!
>
> Therefore, the author does not provide any guarantee or warranty concerning
> to correctness, functionality or performance and does not accept any liability
> for damage caused by this application, examples or mentioned information.
>
> **Thus, use it on your own risk!**


### Wanna support me?

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/N362PLZ)


## Installation

You can install or upgrade `htknx` with:

```
$ pip install htknx --upgrade
```

Or you can install from source with:

```
$ git clone https://github.com/dstrigl/htknx.git
$ cd htknx
$ python setup.py install
```


## Usage

```
usage: htknx [-h] [--logging-config LOGGING_CONFIG] [config_file]

Heliotherm heat pump KNX gateway, v0.1.0.

  https://github.com/dstrigl/htknx

positional arguments:
  config_file           the filename under which the gateway settings can be
                        found, default: htknx.yaml

optional arguments:
  -h, --help            show this help message and exit
  --logging-config LOGGING_CONFIG
                        the filename under which the logging configuration can
                        be found, default: logging.conf

DISCLAIMER
----------
  Please note that any incorrect or careless usage of this program as well as
  errors in the implementation can damage your heat pump!
  Therefore, the author does not provide any guarantee or warranty concerning
  to correctness, functionality or performance and does not accept any liability
  for damage caused by this program or mentioned information.
  Thus, use it on your own risk!

```


### Example

```
$ htknx /home/pi/my-htknx.yaml

TODO
...
```


### Configuration

`htknx` is controlled via a configuration file. Per default the configuration file is named `htknx.yaml`.

The configuration file can contain the following four sections:

* The `general` section can contain:

    * `update_interval` the update interval to refresh the heat pump parameters (optional, default: `60` seconds)
    * `cyclic_sending_interval` the time interval for data points that are to be sent cyclically to the KNX bus (optional, default: `10` minutes)

* The `heat_pump` section is needed to specify the connection to the heat pump:

    * `device` the serial device on which the heat pump is connected (e.g. `/dev/ttyUSB0`)
    * `baudrate` baudrate of the serial connection to the heat pump (same as configured on the heat pump, e.g. `19200`)

* The `knx` section is needed to specify the connection to the KNX interface:

    * `gateway_ip` the ip address of the KNX tunneling interface (e.g. `192.168.11.81`)
    * `gateway_port` the port the KNX tunneling interface is listening on (optional, default: `3671`)
    * `auto_reconnect` determines whether to try a reconnect if the connection to the KNX tunneling interface could not be established (optional, default: `true`)
    * `auto_reconnect_wait` the time to wait for the next auto reconnect (optional, default: `3` seconds)
    * `local_ip` the local ip address that is used by htknx (e.g. `192.168.11.114`)
    * `own_address` the individual (physical) address of the htknx daemon (optional, default: `15.15.250`)
    * `rate_limit` a rate limit for telegrams sent to the KNX bus per second (optional, default: `10`)

* The `data_points` section contains the data points from the heat pump which should be provided to the KNX bus:

    * 'Parameter Name'
    * `value_type`
    * `group_address` the KNX group address of the data point (e.g. `1/2/3`)
    * `writable` determines whether the data point could also be written (optional, default: `false`)
    * `cyclic_sending` determines whether the data point should be sent cyclically to the KNX bus (optional, default: `false`)
    * `send_on_change` defines whether the data point should be sent to the KNX bus if it changes for a defined value (optional, default: `false`)
    * `on_change_of_absolute` the absolute value of change for sending on change (e.g. `0.5` for 0.5°C)
    * `on_change_of_relative` the relative value of change for sending on change (in percent, e.g. `10` for 10%)


## Credits

* Project dependencies scanned by [PyUp.io](https://pyup.io).


## License

Distributed under the terms of the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
