# Hue-sensors-HASS
Component for Hue sensors in Home-assistant.

Place the custom_components folder in your configuration directory (or add its contents to an existing custom_components folder). Please note you are adding a hub and the sensors in the config instructions below, both are required. Additionally setup assumes have the file phue.conf in your hass config dir, which is created by the hue lights component (different author). Hopefully the sensors and lights can be unified with some more work.

Hue dimmer remotes can be used for a click and long press (hold button for 2 sec and see LED blink twice).

Add to your config:

```
hue:

sensor:
  - platform: hue
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

## Multiway sensors
Multiway sensors is a traditional way to have several switches work in correspondence to control the same group of lights.
It you want to use more than one Hue sensor obtain the same effect of controlling the _same_ light automations (say two switches at either end of your living room), it is hard to make automations and state work well trying to handle the two sensors individually.
Therefore, a synthetic sensor type - the multiway sensor - is provided, that looks at several sensors and returns the latest seen state from the combined set of monitored sensors. One can then write automations that look at the state of the single multiway sensor instead of at the individual states of the participating sensors.

To add a multiway sensor, extend your configuration as follows:

```
hue:

sensor:
  - platform: hue
    multiwaysensors: 
      - name: Multiway Sensor Name 1
        sensorids: sensor.hue_sensor_1, sensor.hue_sensor_2
      - name: Multiway Sensor Name 2
        sensorids: sensor.hue_sensor_3, sensor.hue_sensor_4
```
where sensor.hue_sensor_1 etc. are the entity ids of the real sensors and Multiway Sensor Name 1 etc. are the friendly names of your multiway sensors.



<img src="https://github.com/robmarkcole/Hue-sensors-HASS/blob/master/hue.png">
