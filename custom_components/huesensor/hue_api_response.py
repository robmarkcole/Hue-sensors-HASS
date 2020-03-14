"""Hue API data parsing for sensors."""
from typing import Any, Callable, Iterable, Dict, Optional, Tuple

from homeassistant.const import STATE_OFF, STATE_ON

BINARY_SENSOR_MODELS = ("SML",)
ENTITY_ATTRS = {
    "SML": [
        "light_level",
        "battery",
        "last_updated",
        "lx",
        "dark",
        "daylight",
        "temperature",
        "on",
        "reachable",
        "sensitivity",
        "threshold_dark",
        "threshold_offset",
    ],
}


def parse_sml(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the json for a SML Hue motion sensor and return the data."""
    data = {}
    if response["type"] == "ZLLLightLevel":
        lightlevel = response["state"]["lightlevel"]
        tholddark = response["config"]["tholddark"]
        tholdoffset = response["config"]["tholdoffset"]
        if lightlevel is not None:
            lx = round(float(10 ** ((lightlevel - 1) / 10000)), 2)
            dark = response["state"]["dark"]
            daylight = response["state"]["daylight"]
            data = {
                "light_level": lightlevel,
                "lx": lx,
                "dark": dark,
                "daylight": daylight,
                "threshold_dark": tholddark,
                "threshold_offset": tholdoffset,
            }
        else:
            data = {
                "light_level": "No light level data",
                "lx": None,
                "dark": None,
                "daylight": None,
                "threshold_dark": None,
                "threshold_offset": None,
            }

    elif response["type"] == "ZLLTemperature":
        temp = response["state"]["temperature"]
        temp = temp / 100.0 if temp is not None else "No temperature data"
        data = {"temperature": temp}

    elif response["type"] == "ZLLPresence":
        name_raw = response["name"]
        arr = name_raw.split()
        arr.insert(-1, "motion")
        name = " ".join(arr)
        hue_state = response["state"]["presence"]
        state = STATE_ON if hue_state is True else STATE_OFF

        data = {
            "model": "SML",
            "name": name,
            "state": state,
            "battery": response["config"]["battery"],
            "on": response["config"]["on"],
            "reachable": response["config"]["reachable"],
            "sensitivity": response["config"]["sensitivity"],
            "last_updated": response["state"]["lastupdated"].split("T"),
        }
    return data


def parse_hue_api_response(sensors: Iterable[Dict[str, Any]]):
    """Take in the Hue API json response."""
    data_dict = {}  # The list of sensors, referenced by their hue_id.

    # Filter sensors by model.
    for sensor in filter(lambda x: x["modelid"].startswith("SML"), sensors):
        model_id = sensor["modelid"][0:3]
        unique_sensor_id = sensor["uniqueid"]
        _key = model_id + "_" + unique_sensor_id[:-5]
        parsed_sensor = parse_sml(sensor)
        if _key not in data_dict:
            data_dict[_key] = parsed_sensor
        else:
            data_dict[_key].update(parsed_sensor)

    return data_dict
