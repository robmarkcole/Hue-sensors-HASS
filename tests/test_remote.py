"""Tests for remote.py."""
import logging

import pytest

from custom_components.huesensor.hue_api_response import (
    parse_hue_api_response,
    parse_rwl,
    parse_zgp,
    parse_z3_rotary,
)

from .sensor_samples import (
    MOCK_RWL, 
    MOCK_ZGP,
    MOCK_Z3_ROTARY,
    PARSED_RWL,
    PARSED_ZGP,
    PARSED_Z3_ROTARY,
)


@pytest.mark.parametrize(
    "raw_response, sensor_key, parsed_response, parser_func",
    (
        (MOCK_ZGP, "ZGP_00:44:23:08", PARSED_ZGP, parse_zgp),
        (MOCK_RWL, "RWL_00:17:88:01:10:3e:3a:dc-02", PARSED_RWL, parse_rwl),
        (
            MOCK_Z3_ROTARY,
            "Z3-_ff:ff:00:0f:e7:fd:ba:b7-01-fc00",
            PARSED_Z3_ROTARY,
            parse_z3_rotary,
        ),
    ),
)
def test_parse_remote_raw_data(
    raw_response, sensor_key, parsed_response, parser_func, caplog
):
    """Test data parsers for known remotes and check behavior for unknown."""
    assert parser_func(raw_response) == parsed_response
    unknown_sensor_data = {"modelid": "new_one", "uniqueid": "ff:00:11:22"}
    with caplog.at_level(level=logging.WARNING):
        assert parse_hue_api_response(
            [raw_response, unknown_sensor_data, raw_response]
        ) == {sensor_key: parsed_response}
        assert len(caplog.messages) == 1
