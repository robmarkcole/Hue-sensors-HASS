# Hue-sensors-HASS
Component for Hue sensors in Home-assistant.

Place the custom_components folder in your configuration directory (or add its contents to an existing custom_components folder). Please note you are adding a hub and the sensors in the config instructions below, both are required. Additionally setup assumes have the file phue.conf in your hass config dir, which is created by the hue lights component (different author). Hopefully the sensors and lights can be unified with some more work.

Hue dimmer remotes can be used for a click and long press (hold button for 2 sec and see LED blink twice).

Add to your config:

```
hue_sensor:

sensor:
  - platform: hue_sensor
```

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
