# htknx

[![PyPI version](https://img.shields.io/pypi/v/htknx.svg)](https://pypi.org/project/htknx)
[![Python versions](https://img.shields.io/pypi/pyversions/htknx.svg)](https://pypi.org/project/htknx)
[![License](https://img.shields.io/pypi/l/htknx.svg)](https://pypi.org/project/htknx)
[![Build status](https://github.com/dstrigl/HtREST/workflows/CI/badge.svg)](https://github.com/dstrigl/htknx/actions?query=workflow%3ACI)
[![Updates](https://pyup.io/repos/github/dstrigl/htknx/shield.svg)](https://pyup.io/repos/github/dstrigl/htknx)

![KNX](knx-logo.png)

[Heliotherm](http://www.heliotherm.com/) heat pump [KNX](https://www.knx.org) gateway for Python 3.7 and 3.8.

Can be used to provide the different [Heliotherm heat pump parameters](https://htheatpump.readthedocs.io/en/latest/htparams.html) as data points to the KNX bus.


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


## Setup

The following diagram shows the schematic view of a possible setup:

![Setup](setup.png)


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


### Example:

```
$ htknx /home/pi/my-htknx.yaml
HTHEATPUMP: load parameter definitions from: /home/pi/venv/htknx/lib/python3.7/site-packages/htheatpump-1.3.1-py3.7.egg/htheatpump/htparams.csv
Namespace(config_file='/home/pi/my-htknx.yaml', logging_config='/home/pi/prog/htknx/htknx/logging.conf')
2021-01-27 17:14:35,736 INFO [htknx.__main__|main_async]: Load settings from '/home/pi/my-htknx.yaml'.
2021-01-27 17:14:36,394 INFO [htknx.__main__|main_async]: Start Heliotherm heat pump KNX gateway v0.1.0.
2021-01-27 17:14:36,505 INFO [htknx.__main__|main_async]: Connected successfully to heat pump with serial number 123456.
2021-01-27 17:14:36,551 INFO [htknx.__main__|main_async]: Software version = 3.0.20 (2321)
2021-01-27 17:14:36,587 WARNING [xknx.log|loop_until_sigint]: Press Ctrl+C to stop
2021-01-27 17:14:36,592 INFO [htknx.__main__|login_loop]: <<< [ LOGIN (every 0:00:30) ] >>>
2021-01-27 17:14:36,598 INFO [htknx.__main__|update_loop]: <<< [ UPDATE (every 0:00:25) ] >>>
2021-01-27 17:14:36,604 INFO [htknx.__main__|cyclic_sending_loop]: <<< [ CYCLIC SENDING (every 0:01:00) ] >>>
2021-01-27 17:14:36,608 INFO [htknx.__main__|cyclic_sending_loop]: Sending: ['Temp. Aussen', 'Stoerung']
2021-01-27 17:14:37,152 INFO [htknx.__main__|update_loop]: Update: {'Betriebsart': 1, 'HKR Soll_Raum': 22.0, 'WW Normaltemp.': 50, 'BSZ Verdichter Betriebsst. ges': 12000, 'Temp. Aussen': -2.6, 'Temp. Frischwasser_Istwert': 43.6, 'Heizkreispumpe': True, 'Stoerung': False}
2021-01-27 17:14:37,156 INFO [htknx.htdatapoint|set]: Update and send DP 'Betriebsart' [1/7/9]: value=1 (send_on_change: True, on_change_of_absolute: 1, on_change_of_relative: None, last_sent_value: None)
2021-01-27 17:14:37,161 INFO [htknx.htdatapoint|set]: Update and send DP 'HKR Soll_Raum' [1/7/10]: value=22.0 (send_on_change: True, on_change_of_absolute: 0.1, on_change_of_relative: None, last_sent_value: None)
2021-01-27 17:14:37,165 INFO [htknx.htdatapoint|set]: Update and send DP 'WW Normaltemp.' [1/7/17]: value=50 (send_on_change: True, on_change_of_absolute: 1, on_change_of_relative: None, last_sent_value: None)
2021-01-27 17:14:37,170 INFO [htknx.htdatapoint|set]: Update and send DP 'Temp. Frischwasser_Istwert' [1/7/45]: value=43.6 (send_on_change: True, on_change_of_absolute: None, on_change_of_relative: 10, last_sent_value: None)
2021-01-27 17:15:02,181 INFO [htknx.__main__|update_loop]: <<< [ UPDATE (every 0:00:25) ] >>>
2021-01-27 17:15:02,633 INFO [htknx.__main__|update_loop]: Update: {'Betriebsart': 1, 'HKR Soll_Raum': 22.0, 'WW Normaltemp.': 50, 'BSZ Verdichter Betriebsst. ges': 12001, 'Temp. Aussen': -2.6, 'Temp. Frischwasser_Istwert': 43.6, 'Heizkreispumpe': True, 'Stoerung': False}
2021-01-27 17:15:06,641 INFO [htknx.__main__|login_loop]: <<< [ LOGIN (every 0:00:30) ] >>>
2021-01-27 17:15:27,662 INFO [htknx.__main__|update_loop]: <<< [ UPDATE (every 0:00:25) ] >>>
2021-01-27 17:15:28,107 INFO [htknx.__main__|update_loop]: Update: {'Betriebsart': 1, 'HKR Soll_Raum': 22.0, 'WW Normaltemp.': 50, 'BSZ Verdichter Betriebsst. ges': 12001, 'Temp. Aussen': -2.6, 'Temp. Frischwasser_Istwert': 43.6, 'Heizkreispumpe': True, 'Stoerung': False}
2021-01-27 17:15:36,624 INFO [htknx.__main__|cyclic_sending_loop]: <<< [ CYCLIC SENDING (every 0:01:00) ] >>>
2021-01-27 17:15:36,629 INFO [htknx.__main__|cyclic_sending_loop]: Sending: ['Temp. Aussen', 'Stoerung']
2021-01-27 17:15:36,688 INFO [htknx.__main__|login_loop]: <<< [ LOGIN (every 0:00:30) ] >>>
...
```


## Configuration

`htknx` is controlled via a configuration file. Per default the configuration file is named `htknx.yaml`.

The configuration file can contain the following five sections:

* The `general` section can contain:

    * `update_interval` the update interval to refresh the heat pump parameters (optional, default: `60` seconds)
    * `cyclic_sending_interval` the time interval for data points that are to be sent cyclically to the KNX bus (optional, default: `10` minutes)
    * `synchronize_clock_weekly` to define the day of the week (`mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`) and the time (e.g. `'19:55'`) to synchronize the heat pump clock regularly (optional, default: disabled)

* The `heat_pump` section is needed to specify the connection to the heat pump:

    * `device` the serial device on which the heat pump is connected (e.g. `/dev/ttyUSB0`)
    * `baudrate` baudrate of the serial connection to the heat pump (same as configured on the heat pump, e.g. `19200`)

* The `knx` section is needed to specify the connection to the KNX interface (e.g. a [Weinzierl KNX IP Interface 731](https://www.weinzierl.de/index.php/de/alles-knx1/knx-devices/knx-ip-interface-731-de)):

    * `gateway_ip` the ip address of the KNX tunneling interface (e.g. `192.168.11.81`)
    * `gateway_port` the port the KNX tunneling interface is listening on (optional, default: `3671`)
    * `auto_reconnect` determines whether to try a reconnect if the connection to the KNX tunneling interface could not be established (optional, default: `true`)
    * `auto_reconnect_wait` the time to wait for the next auto reconnect (optional, default: `3` seconds)
    * `local_ip` the local ip address that is used to connect to the KNX tunneling interface (optional, e.g. `192.168.11.114`)
    * `own_address` the individual (physical) address of this gateway (optional, default: `15.15.250`)
    * `rate_limit` a rate limit for telegrams sent to the KNX bus per second (optional, default: `10`)

* The `data_points` section contains the dictionary of [heat pump parameters](https://htheatpump.readthedocs.io/en/latest/htparams.html) for which a data point should be provided to the KNX bus.

  Each item in the dictionary consists of the "parameter name" as key and the following properties:

    * `value_type` the value type of the data point (e.g. `binary`, `common_temperature`, `1byte_unsigned`, `4byte_unsigned`, etc. as supported by [XKNX](https://github.com/XKNX/xknx))
    * `group_address` the KNX group address of the data point (e.g. `1/2/3`)
    * `writable` determines whether the data point could also be written or not (optional, default: `false`)
    * `cyclic_sending` determines whether the data point should be sent cyclically to the KNX bus (optional, default: `false`)
    * `send_on_change` defines whether the data point should be sent to the KNX bus if it changes for a defined value (optional, default: `false`)
    * `on_change_of_absolute` the absolute value of change for sending on change (e.g. `0.5` for 0.5°C)
    * `on_change_of_relative` the relative value of change for sending on change (in percent, e.g. `10` for 10%)

  A list of supported value types can be found in the comments of the [configuration template](https://github.com/dstrigl/htknx/blob/master/htknx/htknx-template.yaml) or [sample configuration file](https://github.com/dstrigl/htknx/blob/master/htknx/htknx.yaml). These are exactly the same value types supported by the [XKNX](https://github.com/XKNX/xknx) module on which this project is based.

* The `notifications` section contains the setup of the different supported notifications (optional).

  At the moment the following notifications are supported:

  * `on_malfunction` which sends a notification with the current error message (as DPT-16.000) to the KNX bus if the heat pump is malfunctioning:

      * `group_address` the KNX group address under which the error message is sent (e.g. `1/2/255`)
      * `repeat_after` the time interval until the notification should be repeated if the heat pump is still malfunctioning (optional, e.g.  `10` minutes)


### Sample configuration:

The following block shows a sample configuration for the heat pump parameters

  * *Betriebsart*,
  * *HKR Soll_Raum*,
  * *WW Normaltemp.*,
  * *BSZ Verdichter Betriebsst. ges*,
  * *Temp. Aussen*,
  * *Temp. Frischwasser_Istwert*,
  * *Heizkreispumpe* and
  * *Stoerung*.

These heat pump parameters are updated every 25 seconds and some of them are sent cyclically to the KNX bus every minute, while some of the other parameters are sent immediately after a change.

Only the three parameters *"Betriebsart"*, *"HKR Soll_Raum"* and *"WW Normaltemp."* are writable.

In addition, a notification with the current error message is sent to the KNX bus if the heat pump is malfunctioning.

```
general:
  update_interval:
    seconds: 25
  cyclic_sending_interval:
    minutes: 1
#  synchronize_clock_weekly:
#    weekday: tue  # mon, tue, wed, thu, fri, sat, sun
#    time: '13:05'

heat_pump:
  device: /dev/ttyUSB0
  baudrate: 115200

knx:
  gateway_ip: '192.168.11.81'
  rate_limit: 10
#  gateway_port: 3671
#  auto_reconnect: True
#  auto_reconnect_wait:
#    seconds: 3
#  local_ip: '192.168.11.140'
#  own_address: '15.15.250'

data_points:
  # https://htheatpump.readthedocs.io/en/latest/htparams.html
  # -----------------------------------------------------------------
  'Betriebsart':
    # 0 = Aus
    # 1 = Automatik
    # 2 = Kühlen
    # 3 = Sommer
    # 4 = Dauerbetrieb
    # 5 = Absenkung
    # 6 = Urlaub
    # 7 = Party
    value_type: '1byte_unsigned'  # DPT-5.005 (Dezimalfaktor 0..255)
    group_address: '1/7/9'
    writable: true
    send_on_change: true
    on_change_of_absolute: 1
  # -----------------------------------------------------------------
  'HKR Soll_Raum':
    # MIN: 10.0
    # MAX: 25.0
    value_type: 'common_temperature'  # DPT-14.068 (Temperatur °C)
    group_address: '1/7/10'
    writable: true
    send_on_change: true
    on_change_of_absolute: 0.1
  # -----------------------------------------------------------------
  'WW Normaltemp.':
    # MIN: 10
    # MAX: 75
    value_type: '1byte_unsigned'  # DPT-5.005 (Dezimalfaktor 0..255)
    # or:
    # value_type: 'common_temperature'  # DPT-14.068 (Temperatur °C)
    group_address: '1/7/17'
    writable: true
    send_on_change: true
    on_change_of_absolute: 1
  # -----------------------------------------------------------------
  'BSZ Verdichter Betriebsst. ges':
    # MIN: 0
    # MAX: 100000
    value_type: '4byte_unsigned'  # DPT-12.102 (Zähler Zeit Stunden)
    group_address: '1/7/31'
  # -----------------------------------------------------------------
  'Temp. Aussen':
    # MIN: -20.0
    # MAX: 40.0
    value_type: 'common_temperature'  # DPT-14.068 (Temperatur °C)
    group_address: '1/7/36'
    cyclic_sending: true
  # -----------------------------------------------------------------
  'Temp. Frischwasser_Istwert':
    # MIN: 0.0
    # MAX: 70.0
    value_type: 'common_temperature'  # DPT-14.068 (Temperatur °C)
    group_address: '1/7/45'
    send_on_change: true
    on_change_of_relative: 10
  # -----------------------------------------------------------------
  'Heizkreispumpe':
    # MIN: 0
    # MAX: 1
    value_type: 'binary'  # DPT-1.011 (Status)
    group_address: '1/7/51'
    send_on_change: true
  # -----------------------------------------------------------------
  'Stoerung':
    # MIN: 0
    # MAX: 1
    value_type: 'binary'  # DPT-1.005 (Alarm)
    group_address: '1/7/56'
    cyclic_sending: true

notifications:
  on_malfunction:
    group_address: '1/7/255'  # DPT-16.000 (Zeichen ASCII)
    repeat_after:
      minutes: 10
```

The following image shows a screenshot of the [Group Monitor](https://support.knx.org/hc/en-us/articles/360011717719-Monitor) of the [ETS application](https://www.knx.org/knx-en/for-professionals/software/ets-5-professional/) with the data points provided by the upper [sample configuration](https://github.com/dstrigl/htknx/blob/master/htknx/htknx.yaml):

![ETS Group Monitor](group-monitoring.png)


## Credits

* [XKNX](https://xknx.io/) - Asynchronous Python Library for KNX
* Project dependencies scanned by [PyUp.io](https://pyup.io)


## License

Distributed under the terms of the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
