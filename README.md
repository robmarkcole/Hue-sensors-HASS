# Hue-sensors-HASS
Component for Hue sensors in Home-assistant v0.60 and above.

**To use the dev-phue branch you need to use the edited version of components/hue.py in the custom_components folder. The edits are listed at the bottom of this readme.**

Place the custom_components folder in your configuration directory (or add its contents to an existing custom_components folder).

Hue dimmer remotes can be used for a click and long press (hold button for 2 sec and see LED blink twice).

Add to your config:

```
sensor:
  - platform: hue
```

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

## Changes to components/hue

Changes to components/hue.py

On line 192
```
discovery.load_platform(
            self.hass, 'light', DOMAIN,
            {'bridge_id': socket.gethostbyname(self.host)})
```

Becomes
```
PLATFORMS = ['light', 'sensor']

for platform in PLATFORMS:
     discovery.load_platform(
        self.hass, platform, DOMAIN,
        {'bridge_id': socket.gethostbyname(self.host)})
