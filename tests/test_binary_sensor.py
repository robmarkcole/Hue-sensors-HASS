"""Tests for binary_sensor.py."""
import logging

import pytest

from custom_components.huesensor.hue_api_response import (
    parse_hue_api_response,
    parse_sml,
)

from .sensor_samples import (
    MOCK_ZLLLightlevel,
    MOCK_ZLLPresence,
    MOCK_ZLLTemperature,
    PARSED_ZLLLightlevel,
    PARSED_ZLLPresence,
    PARSED_ZLLTemperature,
)


@pytest.mark.parametrize(
    "raw_response, sensor_key, parsed_response, parser_func",
    (
        (
            MOCK_ZLLPresence,
            "SML_00:17:88:01:02:00:af:28-02",
            PARSED_ZLLPresence,
            parse_sml,
        ),
        (
            MOCK_ZLLLightlevel,
            "SML_00:17:88:01:02:00:af:28-02",
            PARSED_ZLLLightlevel,
            parse_sml,
        ),
        (
            MOCK_ZLLTemperature,
            "SML_00:17:88:01:02:00:af:28-02",
            PARSED_ZLLTemperature,
            parse_sml,
        ),
    ),
)
def test_parse_sensor_raw_data(
    raw_response, sensor_key, parsed_response, parser_func, caplog
):
    """Test data parsers for known sensors."""
    assert parser_func(raw_response) == parsed_response
    with caplog.at_level(level=logging.WARNING):
        assert (
            parse_hue_api_response([raw_response]) 
            == {sensor_key: parsed_response}
        )
        assert len(caplog.messages) == 0
