"""Test throttle back-off logic."""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.entur_sx.const import (
    BACKOFF_INITIAL,
    BACKOFF_MAX,
    BACKOFF_MULTIPLIER,
    BACKOFF_RESET_AFTER,
    UPDATE_INTERVAL,
)
from custom_components.entur_sx.coordinator import EnturSXDataUpdateCoordinator


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    return hass


@pytest.fixture
def mock_api():
    """Create a mock API client."""
    api = MagicMock()
    api.set_session = MagicMock()
    return api


def test_backoff_calculation():
    """Test that back-off times increase exponentially."""
    # First throttle: 2 minutes
    backoff_1 = min(
        BACKOFF_INITIAL * (BACKOFF_MULTIPLIER ** 0),
        BACKOFF_MAX,
    )
    assert backoff_1 == 120
    
    # Second throttle: 2 * 2.5 = 5 minutes
    backoff_2 = min(
        BACKOFF_INITIAL * (BACKOFF_MULTIPLIER ** 1),
        BACKOFF_MAX,
    )
    assert backoff_2 == 300
    
    # Third throttle: 2 * 2.5^2 = 12.5 minutes -> capped at 10 minutes
    backoff_3 = min(
        BACKOFF_INITIAL * (BACKOFF_MULTIPLIER ** 2),
        BACKOFF_MAX,
    )
    assert backoff_3 == 600  # Capped at BACKOFF_MAX


@pytest.mark.asyncio
async def test_throttle_preserves_state(mock_hass, mock_api):
    """Test that throttle returns cached data instead of failing."""
    with patch('custom_components.entur_sx.coordinator.async_get_clientsession'):
        coordinator = EnturSXDataUpdateCoordinator(mock_hass, mock_api)
        
        # Simulate successful data fetch first
        test_data = {"SKY:Line:1": [{"status": "open", "summary": "Test"}]}
        mock_api.async_get_deviations = AsyncMock(return_value=test_data)
        
        # First update should succeed and cache data
        result = await coordinator._async_update_data()
        assert result == test_data
        assert coordinator._cached_data == test_data
        assert coordinator._throttle_count == 0
        
        # Now simulate 429 error
        error_429 = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=429,
            message="Too Many Requests",
        )
        mock_api.async_get_deviations = AsyncMock(side_effect=error_429)
        
        # Should return cached data instead of raising
        result = await coordinator._async_update_data()
        assert result == test_data  # Same cached data
        assert coordinator._throttle_count == 1
        assert coordinator._in_backoff is True
        assert coordinator.update_interval == timedelta(seconds=120)


@pytest.mark.asyncio
async def test_throttle_without_cache_fails(mock_hass, mock_api):
    """Test that throttle without cached data raises UpdateFailed."""
    with patch('custom_components.entur_sx.coordinator.async_get_clientsession'):
        coordinator = EnturSXDataUpdateCoordinator(mock_hass, mock_api)
        
        # No previous successful fetch - no cache
        assert coordinator._cached_data is None
        
        # Simulate 429 error on first fetch
        error_429 = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=429,
            message="Too Many Requests",
        )
        mock_api.async_get_deviations = AsyncMock(side_effect=error_429)
        
        # Should raise UpdateFailed
        from homeassistant.helpers.update_coordinator import UpdateFailed
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_recovery_resets_interval(mock_hass, mock_api):
    """Test that successful recovery resets update interval."""
    with patch('custom_components.entur_sx.coordinator.async_get_clientsession'):
        coordinator = EnturSXDataUpdateCoordinator(mock_hass, mock_api)
        
        # Simulate throttle state
        coordinator._in_backoff = True
        coordinator._throttle_count = 2
        coordinator.update_interval = timedelta(seconds=300)
        
        test_data = {"SKY:Line:1": [{"status": "open", "summary": "Test"}]}
        mock_api.async_get_deviations = AsyncMock(return_value=test_data)
        
        # Successful fetch should reset interval
        result = await coordinator._async_update_data()
        assert result == test_data
        assert coordinator._in_backoff is False
        assert coordinator.update_interval == timedelta(seconds=UPDATE_INTERVAL)


@pytest.mark.asyncio
async def test_throttle_count_resets_after_success_period(mock_hass, mock_api):
    """Test that throttle count resets after 30 minutes of success."""
    with patch('custom_components.entur_sx.coordinator.async_get_clientsession'):
        coordinator = EnturSXDataUpdateCoordinator(mock_hass, mock_api)
        
        # Set up previous throttle state
        coordinator._throttle_count = 3
        coordinator._last_success_time = datetime.now() - timedelta(
            seconds=BACKOFF_RESET_AFTER + 60
        )
        
        test_data = {"SKY:Line:1": [{"status": "open", "summary": "Test"}]}
        mock_api.async_get_deviations = AsyncMock(return_value=test_data)
        
        # Successful fetch after long success period
        result = await coordinator._async_update_data()
        assert result == test_data
        assert coordinator._throttle_count == 0  # Reset


if __name__ == "__main__":
    # Run basic calculation test
    test_backoff_calculation()
    print("✓ Back-off calculation test passed")
    print(f"  - 1st throttle: {BACKOFF_INITIAL}s (2 min)")
    print(f"  - 2nd throttle: {int(BACKOFF_INITIAL * BACKOFF_MULTIPLIER)}s (5 min)")
    print(f"  - 3rd throttle: {BACKOFF_MAX}s (10 min, capped)")
    print(f"  - Reset after: {BACKOFF_RESET_AFTER}s (30 min)")
