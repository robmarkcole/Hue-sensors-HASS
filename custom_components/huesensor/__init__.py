"""The huesensors component."""
from typing import List

from homeassistant.components.hue import DOMAIN as HUE_DOMAIN, HueBridge


def get_bridges(hass) -> List[HueBridge]:
    """Retrieve Hue bridges from loaded official Hue integration."""
    return [
        entry
        for entry in hass.data[HUE_DOMAIN].values()
        if isinstance(entry, HueBridge) and entry.api
    ]
