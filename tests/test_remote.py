"""
Tests for binary_sensor.py
"""
import custom_components.huesensor.remote as remote

MOCK_ZGP = {
    "state": {"buttonevent": 17, "lastupdated": "2019-06-22T14:43:50"},
    "swupdate": {"state": "notupdatable", "lastinstall": None},
    "config": {"on": True},
    "name": "Hue Tap",
    "type": "ZGPSwitch",
    "modelid": "ZGPSWITCH",
    "manufacturername": "Philips",
    "productname": "Hue tap switch",
    "diversityid": "d8cde5d5-0eef-4b95-b0f0-71ddd2952af4",
    "uniqueid": "00:00:00:00:00:44:23:08-f2",
    "capabilities": {
        "certified": True,
        "primary": True,
        "inputs": [
            {
                "repeatintervals": [],
                "events": [{"buttonevent": 34, "eventtype": "initial_press"}],
            },
            {
                "repeatintervals": [],
                "events": [{"buttonevent": 16, "eventtype": "initial_press"}],
            },
            {
                "repeatintervals": [],
                "events": [{"buttonevent": 17, "eventtype": "initial_press"}],
            },
            {
                "repeatintervals": [],
                "events": [{"buttonevent": 18, "eventtype": "initial_press"}],
            },
        ],
    },
}

PARSED_ZGP = {
    "last_button_event": "3_click",
    "last_updated": ["2019-06-22", "14:43:50"],
    "model": "ZGP",
    "name": "Hue Tap",
    "state": "3_click",
}


def test_parse_zgp():
    assert remote.parse_zgp(MOCK_ZGP) == PARSED_ZGP
