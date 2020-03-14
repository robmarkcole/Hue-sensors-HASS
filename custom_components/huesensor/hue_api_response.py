"""Hue API data parsing for sensors."""
import logging
from typing import Any, Callable, Iterable, Dict, Optional, Tuple

from homeassistant.const import STATE_OFF, STATE_ON

REMOTE_MODELS = ("RWL", "ROM", "FOH", "ZGP", "Z3-")
BINARY_SENSOR_MODELS = ("SML",)
ENTITY_ATTRS = {
    "RWL": ["last_updated", "last_button_event", "battery", "on", "reachable"],
    "ROM": ["last_updated", "last_button_event", "battery", "on", "reachable"],
    "ZGP": ["last_updated", "last_button_event"],
    "FOH": ["last_updated", "last_button_event"],
    "Z3-": [
        "last_updated",
        "last_button_event",
        "battery",
        "on",
        "reachable",
        "dial_state",
        "dial_position",
        "software_update",
    ],
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
FOH_BUTTONS = {
    16: "left_upper_press",
    20: "left_upper_release",
    17: "left_lower_press",
    21: "left_lower_release",
    18: "right_lower_press",
    22: "right_lower_release",
    19: "right_upper_press",
    23: "right_upper_release",
    100: "double_upper_press",
    101: "double_upper_release",
    98: "double_lower_press",
    99: "double_lower_release",
}
RWL_RESPONSE_CODES = {
    "0": "_click",
    "1": "_hold",
    "2": "_click_up",
    "3": "_hold_up",
}
TAP_BUTTONS = {34: "1_click", 16: "2_click", 17: "3_click", 18: "4_click"}
Z3_BUTTON = {
    1000: "initial_press",
    1001: "repeat",
    1002: "short_release",
    1003: "long_release",
}
Z3_DIAL = {1: "begin", 2: "end"}


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
        if response["state"]["temperature"] is not None:
            data = {"temperature": response["state"]["temperature"] / 100.0}
        else:
            data = {"temperature": "No temperature data"}

    elif response["type"] == "ZLLPresence":
        name_raw = response["name"]
        arr = name_raw.split()
        arr.insert(-1, "motion")
        name = " ".join(arr)
        hue_state = response["state"]["presence"]
        if hue_state is True:
            state = STATE_ON
        else:
            state = STATE_OFF

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
