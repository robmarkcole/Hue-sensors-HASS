"""
Tests for binary_sensor.py
"""
import json
import custom_components.huesensor.binary_sensor as bs

MOCK_ZLLPresence = {
    "state": {"presence": False, "lastupdated": "2020-02-06T07:28:08"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-05-06T13:14:45"},
    "config": {
        "on": True,
        "battery": 58,
        "reachable": True,
        "alert": "lselect",
        "sensitivity": 2,
        "sensitivitymax": 2,
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Living room sensor",
    "type": "ZLLPresence",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue motion sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:17:88:01:02:00:af:28-02-0406",
    "capabilities": {"certified": True, "primary": True},
}

MOCK_ZLLLightlevel = {
    "state": {
        "lightlevel": 0,
        "dark": True,
        "daylight": False,
        "lastupdated": "2020-02-06T07:26:02",
    },
    "swupdate": {"state": "noupdates", "lastinstall": "2019-05-06T13:14:45"},
    "config": {
        "on": True,
        "battery": 58,
        "reachable": True,
        "alert": "none",
        "tholddark": 16000,
        "tholdoffset": 7000,
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue ambient light sensor 1",
    "type": "ZLLLightLevel",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue ambient light sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:17:88:01:02:00:af:28-02-0400",
    "capabilities": {"certified": True, "primary": False},
}

MOCK_ZLLTemperature = {
    "state": {"temperature": 1744, "lastupdated": "2020-02-06T07:26:26"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-05-06T13:14:45"},
    "config": {
        "on": True,
        "battery": 58,
        "reachable": True,
        "alert": "none",
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Hue temperature sensor 1",
    "type": "ZLLTemperature",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue temperature sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:17:88:01:02:00:af:28-02-0402",
    "capabilities": {"certified": True, "primary": False},
}

PARSED_ZLLPresence = {
    "battery": 58,
    "last_updated": ["2020-02-06", "07:28:08"],
    "model": "SML",
    "name": "Living room motion sensor",
    "on": True,
    "reachable": True,
    "sensitivity": 2,
    "state": "off",
}

PARSED_ZLLLightlevel = {
    "dark": True,
    "daylight": False,
    "light_level": 0,
    "lx": 1.0,
    "threshold_dark": 16000,
    "threshold_offset": 7000,
}

PARSED_ZLLTemperature = {"temperature": 17.44}


def test_parse_sml():
    assert bs.parse_sml(MOCK_ZLLPresence) == PARSED_ZLLPresence
    assert bs.parse_sml(MOCK_ZLLLightlevel) == PARSED_ZLLLightlevel
    assert bs.parse_sml(MOCK_ZLLTemperature) == PARSED_ZLLTemperature
