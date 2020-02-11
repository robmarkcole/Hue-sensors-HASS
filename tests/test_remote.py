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
    "capabilities": {"certified": True, "primary": True, "inputs": [],},
}

MOCK_RWL = {
    "state": {"buttonevent": 4002, "lastupdated": "2019-12-28T21:58:02"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-10-13T13:16:15"},
    "config": {"on": True, "battery": 100, "reachable": True, "pending": []},
    "name": "Hue dimmer switch 1",
    "type": "ZLLSwitch",
    "modelid": "RWL021",
    "manufacturername": "Philips",
    "productname": "Hue dimmer switch",
    "diversityid": "73bbabea-3420-499a-9856-46bf437e119b",
    "swversion": "6.1.1.28573",
    "uniqueid": "00:17:88:01:10:3e:3a:dc-02-fc00",
    "capabilities": {"certified": True, "primary": True, "inputs": []},
}

PARSED_ZGP = {
    "last_button_event": "3_click",
    "last_updated": ["2019-06-22", "14:43:50"],
    "model": "ZGP",
    "name": "Hue Tap",
    "state": "3_click",
}

PARSED_RWL = {
    "battery": 100,
    "last_button_event": "4_click_up",
    "last_updated": ["2019-12-28", "21:58:02"],
    "model": "RWL",
    "name": "Hue dimmer switch 1",
    "on": True,
    "reachable": True,
    "state": "4_click_up",
}


def test_parse_zgp():
    assert remote.parse_zgp(MOCK_ZGP) == PARSED_ZGP
    assert remote.parse_rwl(MOCK_RWL) == PARSED_RWL
