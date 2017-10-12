# Hue-sensors-HASS
Component (in development) for Hue sensors in Home-assistant.

Place the contents of components in your components directory (this is the hub component), and the contents of components/sensor in components/sensor (the sensors component). Setup assumes have the file phue.conf in your hass config dir.

Hue dimmer remotes can be used for a click and long press (hold button for 2 sec and see LED blink twice).

Add to your config:

```
hue:

sensor:
  - platform: hue
```

<img src="https://github.com/robmarkcole/Hue-sensors-HASS/blob/master/hue.png">
