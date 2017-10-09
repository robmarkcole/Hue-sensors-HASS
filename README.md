# Hue-sensors-HASS
Custom component for Hue sensors in Home-assistant, continues: https://www.hackster.io/robin-cole/hijack-a-hue-remote-to-control-anything-with-home-assistant-5239a4

Place the custom_components folder in your hass config director, and place the contents of components in your components directory (this is the hub component). Setup assumes you have already configured the Hue component and have the file phue.conf in your hass config dir.

Hue remote can be used for a click and long press (hold button for 2 sec and see LED blink twice).

Add to your config:

```
sensor:
  - platform: hue
```

<img src="https://github.com/robmarkcole/Hue-sensors-HASS/blob/master/hue.png">
