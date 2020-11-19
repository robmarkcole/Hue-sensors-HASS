[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# Hue-sensors-HASS
[FOR COMMUNITY SUPPORT PLEASE USE THIS THREAD](https://community.home-assistant.io/t/hue-motion-sensors-remotes-custom-component)

For Hue & Friends of Hue remotes checkout [Hue-remotes-HASS](https://github.com/robmarkcole/Hue-remotes-HASS)

**PLEASE BE ADVISED: you are strongly encouraged to use the official Hue sensor integration, and cease using this custom integration.** 

Longer explanation: sensor support in the official hue integration is more feature-complete than this custom integration, and if you're already using Hue-remotes-HASS, then the refresh rate for sensors in the official integration will be automatically the fastest possible. Since we want to migrate users to the official integration, please do not open feature request issues or create PR adding new functionality to this custom integration, as they will not be considered. This custom integration will remain available until the next breaking change with Home Assistant, at which point this repo will be archived.

## Overview
This custom integration provides support for the official [Hue motion sensors](https://www2.meethue.com/en-us/p/hue-motion-sensor/046677473389) and the Hue device tracker (allows tracking the mobile with the Hue app installed). Note that these sensors [are officially integrated with Home Assistant](https://www.home-assistant.io/integrations/hue/), but a *different* approach is taken in this custom integration. In the official integration the Hue motion sensors are treated as three separate entities per device: one each for motion, light level, and temperature. The approach in this custom integration is to expose the light level and temperature values as attributes of a single `binary_sensor` entity. Also in this custom integration the device data is updated every second, whilst in the official integration data is only every 5 seconds updated. 

**Be advised that the increased update of this custom integration may cause connectivity problems which can result in errors in the official hue integration**, please do not create any issue for this. If you can't live with these errors, do not use this custom integration.

## Installation
Place the `custom_components` folder in your configuration directory (or add its contents to an existing `custom_components` folder). You need to set up your [Hue bridge](https://www.home-assistant.io/integrations/hue) first. Alternatively install via [HACS](https://hacs.xyz/).

## Configuration
Once installed add to your configuration:

```yaml
binary_sensor:
  - platform: huesensor
device_tracker:
  - platform: huesensor
```

As per [this issue](https://github.com/robmarkcole/Hue-sensors-HASS/issues/48) it is recommended to use the default naming options in the Hue app in order to ensure sensible sensor names in HA.

## Front end display
To add the following group to your HA frontend, add the following to `groups.yaml` (obviously editing to use your sensors):

```yaml
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

```yaml
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

## Developers
* Create venv -> `$ python3 -m venv venv`
* Use venv -> `$ source venv/bin/activate`
* Install requirements -> `$ pip install -r requirements.txt` & `$ pip install -r requirements-dev.txt`
* Run tests -> `$ venv/bin/py.test --cov=custom_components tests/ -vv -p no:warnings`
* Black format -> `$ venv/bin/black custom_components/*` (or setup VScode for format on save)

### About GitHub Actions
This repo has GitHub Actions. It tests HACS, Hassfest, and flake8. It automatically pushes formatting with isort and black. See a bit more info [here](https://github.com/KTibow/ha-blueprint#readme).

## Contributors
Please format code usign [Black](https://github.com/psf/black) before opening a pull request.

A big thanks to [Atsuko Ito](https://github.com/yottatsa) and [Eugenio Panadero](https://github.com/azogue) for their many contributions to this work!
