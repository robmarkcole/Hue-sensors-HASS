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
```
