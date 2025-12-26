import pytest
import pytest_asyncio
from switchbot.devices.meter import SwitchbotMeterProCO2
from switchbot.devices.device import SwitchbotOperationError


class DummyBLEDevice:
    """Simple mock BLEDevice with required attributes."""

    def __init__(self, name: str = "DummyDevice", address: str = "00:11:22:33:44:55"):
        self.name = name
        self.address = address


@pytest_asyncio.fixture
async def meter():
    """Create a SwitchbotMeterProCO2 instance with a dummy BLE device."""
    device = DummyBLEDevice()
    return SwitchbotMeterProCO2(device)


@pytest.mark.asyncio
async def test_set_time_success(meter):
    captured = {}

    async def mock_send(command: str):
        captured["cmd"] = command
        # Simulate successful response byte
        return b"\x01"

    # Patch the _send_command method
    meter._send_command = mock_send

    # Example timestamp (0x05F5E100)
    timestamp = 0x05F5E100
    result = await meter.set_time(timestamp)

    assert result is True
    # Expected command: REQ_HEADER (570f) + 0300 + timestamp hex padded to 8 digits
    expected_command = "570f030005f5e100"
    assert captured.get("cmd") == expected_command


@pytest.mark.asyncio
async def test_set_time_error(meter):
    async def mock_send(command: str):
        # Simulate error response byte
        return b"\x00"

    meter._send_command = mock_send

    timestamp = 0x05F5E100
    with pytest.raises(SwitchbotOperationError):
        await meter.set_time(timestamp)
