[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![build status](http://img.shields.io/travis/robmarkcole/Hue-sensors-HASS/master.svg?style=flat)](https://travis-ci.org/robmarkcole/Hue-sensors-HASS)
[![Coverage](https://codecov.io/github/robmarkcole/Hue-sensors-HASS/coverage.svg?branch=master)](https://codecov.io/gh/robmarkcole/Hue-sensors-HASS)
[![Sponsor](https://img.shields.io/badge/sponsor-%F0%9F%92%96-green)](https://github.com/sponsors/robmarkcole)

# Hue-sensors-HASS
[FOR COMMUNITY SUPPORT PLEASE USE THIS THREAD](https://community.home-assistant.io/t/hue-motion-sensors-remotes-custom-component)

## Overview
This custom component provides support for Hue motion sensors, remotes, and some friends of Hue devices.

## Installation

Place the `custom_components` folder in your configuration directory (or add its contents to an existing `custom_components` folder). You need to set up your [Hue bridge](https://www.home-assistant.io/integrations/hue) first. Alternatively install via [HACS](https://hacs.xyz/).

## Configuration

Once installed add to your configuration:

```
binary_sensor:
  - platform: huesensor
remote:
  - platform: huesensor
device_tracker:
  - platform: huesensor
```

Hue dimmer remotes can be used for a click and long press (hold button for 2 sec and see LED blink twice).

As per [this issue](https://github.com/robmarkcole/Hue-sensors-HASS/issues/48) it is recommended to use the default naming options in the Hue app in order to ensure sensible sensor names in HA.

## Front end display

To add the following group to your HA frontend, add the following to `groups.yaml` (obviously editing to use your sensors):

```
default_view:
  view: yes
  entities:
    - group.Hue

Hue:
  entities:
    - binary_sensor.bedroom_motion_sensor
    - binary_sensor.hall_motion_sensor
    - binary_sensor.living_room_motion_sensor
```

Temperature, light level and other data in the sensor attributes can be broken out into their own sensor using a template sensor, for example:

```
- platform: template
  sensors:

    living_room_temperature:
      friendly_name: 'Living room temperature'
      value_template: '{{state_attr("binary_sensor.living_room_motion_sensor", "temperature")}}'
      unit_of_measurement: °C

    living_room_light_level:
      friendly_name: 'Living room light level'
      value_template: '{{state_attr("binary_sensor.living_room_motion_sensor", "lx")}}'
      unit_of_measurement: lux
```

<p align="center">
<img src="https://github.com/robmarkcole/Hue-sensors-HASS/blob/master/hue.png" width="500">
</p>

## Track Updates

This custom component can be tracked with the help of [HACS](https://hacs.xyz/).

## Debugging

If you get an error when using this component, the procedure for debugging is as follows.

1. Open an issue here on Github. Include the error message, release number of the custom component.
2. Download the Hue API response following the instructions [here](https://www.hackster.io/robin-cole/hijack-a-hue-remote-to-control-anything-with-home-assistant-5239a4#toc-hue-api-1). Save into a .json file.
3. Parse the json file using the [hue_sensors package](https://pypi.python.org/pypi/hue-sensors/1.2) and report the device ID (e.g. RWL_06-02) that is causing your issue.

There are a couple of examples of this process in the debugging_issues folder.

## Developers

* Create venv -> `$ python3 -m venv venv`
* Use venv -> `$ source venv/bin/activate`
* Install requirements -> `$ pip install -r requirements.txt` & `$ pip install -r requirements-dev.txt`
* Run tests -> `$ venv/bin/py.test --cov=custom_components tests/ -vv -p no:warnings`
* Black format -> `$ venv/bin/black custom_components/*` (or setup VScode for format on save)

## Contributors

Please format code usign [Black](https://github.com/psf/black) before opening a pull request.

A big thanks to [@yottatsa](https://github.com/yottatsa) for his many contributions to this work, check out his profile!

## ✨ Support this work

https://github.com/sponsors/robmarkcole

If you or your business find this work useful please consider becoming a sponsor at the link above, this really helps justify the time I invest in maintaining this repo. As we say in England, 'every little helps' - thanks in advance!
