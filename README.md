# htknx

[![PyPI version](https://img.shields.io/pypi/v/htknx.svg)](https://pypi.org/project/htknx)
[![Python versions](https://img.shields.io/pypi/pyversions/htknx.svg)](https://pypi.org/project/htknx)
[![License](https://img.shields.io/pypi/l/htknx.svg)](https://pypi.org/project/htknx)
[![Build status](https://img.shields.io/travis/dstrigl/htknx/master?logo=travis)](https://travis-ci.org/dstrigl/htknx)
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
TODO
```


## Credits

* Project dependencies scanned by [PyUp.io](https://pyup.io).


## License

Distributed under the terms of the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
