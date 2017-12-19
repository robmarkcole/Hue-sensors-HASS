# Hue-sensors-HASS
Component for Hue sensors in Home-assistant v0.60 and above.

Place the custom_components folder in your configuration directory (or add its contents to an existing custom_components folder). Setup assumes you have the file phue.conf in your hass config dir, which is created by the hue lights component (different author). Note that in some cases phue.conf may be named differently, for example mine was something like phue-12412523.conf so I copied and pasted this file, then renamed to phue.conf.

Hue dimmer remotes can be used for a click and long press (hold button for 2 sec and see LED blink twice).

Add to your config:

```
sensor:
  - platform: hue_sensor
```

## Hassio
Under hassio with 0.60 I also initially get the error `unable to find hue_sensors`, which I believe is due to [hue_sensors](https://github.com/robmarkcole/Hue-sensors) not being installed.

Solution: download [hue_sensors.py](https://github.com/robmarkcole/Hue-sensors/blob/master/hue_sensors.py) and place in `custom_components/sensors`, restart hassio.

## Front end display

To add the following group to your HA frontend, add the following to groups.yaml (obviously editing to use your sensors):

```
default_view:
  view: yes
  entities:
    - group.Hue

Hue:
  entities:
    - sensor.bedroom_motion_sensor
    - sensor.hall_motion_sensor
    - sensor.living_room_motion_sensor
    - sensor.living_room_temperature
    - sensor.living_room_light_level
    - sensor.living_room_lux
    - sensor.living_room_remote
    - sensor.remote_bedroom
    - sensor.robins_iphone
```

Temperature, light level and other data in the sensor attributes can be broken out into their own sensor using a template sensor, for example:

```
- platform: template
  sensors:
    living_room_temperature:
      friendly_name: 'Living room temperature'
      value_template: '{{states.sensor.living_room_motion_sensor.attributes.temperature}}'
      unit_of_measurement: °C
```

<img src="https://github.com/robmarkcole/Hue-sensors-HASS/blob/master/hue.png">
