"""Tests for device_tracker.py."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from custom_components.huesensor.device_tracker import (
    async_setup_scanner,
    HueDeviceScanner,
)

from .conftest import MockAsyncCounter


async def test_device_tracker_setup(mock_hass_2_bridges):
    """Test platform setup for binary sensors."""
    mock_async_see = MockAsyncCounter()
    with patch(
        "custom_components.huesensor.device_tracker.async_track_time_interval",
        autospec=True,
    ) as mock_track_time:
        await async_setup_scanner(
            mock_hass_2_bridges,
            {"platform": "huesensor", "scan_interval": timedelta(seconds=10)},
            mock_async_see,
        )

        assert mock_track_time.call_count == 1
        assert mock_async_see.call_count == 1


async def test_device_scanner(mock_hass, mock_hass_2_bridges):
    """Test platform setup for binary sensors."""
    mock_async_see = MockAsyncCounter()

    # no sensors
    empty_scanner = HueDeviceScanner(MagicMock(), mock_async_see)
    await empty_scanner.async_update_info()
    assert mock_async_see.call_count == 0

    # sensors, but no geofence data
    scanner = HueDeviceScanner(mock_hass, mock_async_see)
    await scanner.async_update_info()
    assert mock_async_see.call_count == 0

    # 1 geofence in 2nd bridge
    scanner = HueDeviceScanner(mock_hass_2_bridges, mock_async_see)
    await scanner.async_update_info()
    assert mock_async_see.call_count == 1
