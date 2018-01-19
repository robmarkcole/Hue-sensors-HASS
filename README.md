# Hue-sensors-HASS
Component for Hue sensors in Home-assistant v0.62 and above.

**Note that a modified version of the hue hub component (components/hue.py) is used with the edits are listed at the bottom of this readme. The hub component has changed several times between 0.60 and 0.62 and hence there have been a few issues with this custom component. Hopefully the hub component is settled in 0.62.**

Place the custom_components folder in your configuration directory (or add its contents to an existing custom_components folder).

Hue dimmer remotes can be used for a click and long press (hold button for 2 sec and see LED blink twice).

Add to your config:

```
hue:
  bridges:
    - host: 192.168.0.100

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

## Changes to the official hue hub component

Changes to components/hue.py - adds sensors domain in setup() and adds get_sensor() method.

```
discovery.load_platform(
            self.hass, 'light', DOMAIN,
            {'bridge_id': self.bridge_id})
```

Becomes
```
PLATFORMS = ['light', 'sensor']

for platform in PLATFORMS:
     discovery.load_platform(
        self.hass, platform, DOMAIN,
        {'bridge_id': self.bridge_id})

# adds
def get_sensor(self):
    """Get sensor state."""
    return self.bridge.get_sensor()
```
