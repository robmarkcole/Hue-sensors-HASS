"""Hue API data parsing for sensors."""
from typing import Any, Callable, Iterable, Dict, Optional, Tuple

from aiohue.sensors import (
    ZGP_SWITCH_BUTTON_1,
    ZGP_SWITCH_BUTTON_2,
    ZGP_SWITCH_BUTTON_3,
    ZGP_SWITCH_BUTTON_4,
    ZLL_SWITCH_BUTTON_1_INITIAL_PRESS,
    ZLL_SWITCH_BUTTON_2_INITIAL_PRESS,
    ZLL_SWITCH_BUTTON_3_INITIAL_PRESS,
    ZLL_SWITCH_BUTTON_4_INITIAL_PRESS,
    ZLL_SWITCH_BUTTON_1_HOLD,
    ZLL_SWITCH_BUTTON_2_HOLD,
    ZLL_SWITCH_BUTTON_3_HOLD,
    ZLL_SWITCH_BUTTON_4_HOLD,
    ZLL_SWITCH_BUTTON_1_SHORT_RELEASED,
    ZLL_SWITCH_BUTTON_2_SHORT_RELEASED,
    ZLL_SWITCH_BUTTON_3_SHORT_RELEASED,
    ZLL_SWITCH_BUTTON_4_SHORT_RELEASED,
    ZLL_SWITCH_BUTTON_1_LONG_RELEASED,
    ZLL_SWITCH_BUTTON_2_LONG_RELEASED,
    ZLL_SWITCH_BUTTON_3_LONG_RELEASED,
    ZLL_SWITCH_BUTTON_4_LONG_RELEASED,
)
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
RWL_BUTTONS = {
    ZLL_SWITCH_BUTTON_1_INITIAL_PRESS: "1_click",
    ZLL_SWITCH_BUTTON_2_INITIAL_PRESS: "1_click",
    ZLL_SWITCH_BUTTON_3_INITIAL_PRESS: "1_click",
    ZLL_SWITCH_BUTTON_4_INITIAL_PRESS: "1_click",
    ZLL_SWITCH_BUTTON_1_HOLD: "1_hold",
    ZLL_SWITCH_BUTTON_2_HOLD: "2_hold",
    ZLL_SWITCH_BUTTON_3_HOLD: "3_hold",
    ZLL_SWITCH_BUTTON_4_HOLD: "4_hold",
    ZLL_SWITCH_BUTTON_1_SHORT_RELEASED: "1_click_up",
    ZLL_SWITCH_BUTTON_2_SHORT_RELEASED: "2_click_up",
    ZLL_SWITCH_BUTTON_3_SHORT_RELEASED: "3_click_up",
    ZLL_SWITCH_BUTTON_4_SHORT_RELEASED: "4_click_up",
    ZLL_SWITCH_BUTTON_1_LONG_RELEASED: "1_hold_up",
    ZLL_SWITCH_BUTTON_2_LONG_RELEASED: "2_hold_up",
    ZLL_SWITCH_BUTTON_3_LONG_RELEASED: "3_hold_up",
    ZLL_SWITCH_BUTTON_4_LONG_RELEASED: "4_hold_up",
}
TAP_BUTTONS = {
    ZGP_SWITCH_BUTTON_1: "1_click",
    ZGP_SWITCH_BUTTON_2: "2_click",
    ZGP_SWITCH_BUTTON_3: "3_click",
    ZGP_SWITCH_BUTTON_4: "4_click",
}
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


def parse_zgp(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the json response for a ZGPSWITCH Hue Tap."""
    button = TAP_BUTTONS.get(response["state"]["buttonevent"], "No data")

    return {
        "model": "ZGP",
        "name": response["name"],
        "state": button,
        "last_button_event": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }


def parse_rwl(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the json response for a RWL Hue remote."""
    button = RWL_BUTTONS.get(response["state"]["buttonevent"])

    return {
        "model": "RWL",
        "name": response["name"],
        "state": button,
        "battery": response["config"]["battery"],
        "on": response["config"]["on"],
        "reachable": response["config"]["reachable"],
        "last_button_event": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }


def parse_foh(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the JSON response for a FOHSWITCH (type still = ZGPSwitch)."""
    press = response["state"]["buttonevent"]
    button = FOH_BUTTONS.get(press, "No data")

    return {
        "model": "FOH",
        "name": response["name"],
        "state": button,
        "last_button_event": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }


def parse_z3_rotary(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the json response for a Lutron Aurora Rotary Event."""
    turn = response["state"]["rotaryevent"]
    dial = Z3_DIAL.get(turn, "No data")
    dial_position = response["state"]["expectedrotation"]

    return {
        "model": "Z3-",
        "name": response["name"],
        "dial_state": dial,
        "dial_position": dial_position,
        "software_update": response["swupdate"]["state"],
        "battery": response["config"]["battery"],
        "on": response["config"]["on"],
        "reachable": response["config"]["reachable"],
        "last_updated": response["state"]["lastupdated"].split("T"),
    }


def parse_z3_switch(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the json response for a Lutron Aurora."""
    press = response["state"]["buttonevent"]
    button = Z3_BUTTON.get(press, "No data")

    return {
        "last_button_event": button,
        "state": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }


def _ident_raw_sensor(
    raw_sensor_data: Dict[str, Any]
) -> Tuple[Optional[str], Callable]:
    """Identify sensor types and return unique identifier and parser."""
    model_id = raw_sensor_data["modelid"][0:3]
    unique_sensor_id = raw_sensor_data["uniqueid"]

    if model_id == "SML":
        sensor_key = model_id + "_" + unique_sensor_id[:-5]
        return sensor_key, parse_sml

    elif model_id in ("RWL", "ROM"):
        sensor_key = model_id + "_" + unique_sensor_id[:-5]
        return sensor_key, parse_rwl

    elif model_id in ("FOH", "ZGP"):
        # **** New Model ID ****
        # needed for uniqueness
        sensor_key = model_id + "_" + unique_sensor_id[-14:-3]
        if model_id == "FOH":
            return sensor_key, parse_foh

        return sensor_key, parse_zgp

    elif model_id == "Z3-":
        # Newest Model ID / Lutron Aurora / Hue Bridge
        # treats it as two sensors, I wanted them combined
        if raw_sensor_data["type"] == "ZLLRelativeRotary":  # Rotary Dial
            # Rotary key is substring of button
            sensor_key = model_id + "_" + unique_sensor_id[:-5]
            return sensor_key, parse_z3_rotary
        else:
            sensor_key = model_id + "_" + unique_sensor_id
            return sensor_key, parse_z3_switch

    return None, None


def parse_hue_api_response(sensors: Iterable[Dict[str, Any]]):
    """Take in the Hue API json response."""
    data_dict = {}  # The list of sensors, referenced by their hue_id.

    # Loop over all keys (1,2 etc) to identify sensors and get data.
    for sensor in sensors:
        _key, _raw_parser = _ident_raw_sensor(sensor)
        if _key is None:
            continue

        parsed_sensor = _raw_parser(sensor)
        if _key not in data_dict:
            data_dict[_key] = parsed_sensor
        else:
            data_dict[_key].update(parsed_sensor)

    return data_dict
