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

<img src="https://github.com/robmarkcole/Hue-sensors-HASS/blob/master/hue.png">
