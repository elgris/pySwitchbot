from __future__ import annotations

from .device import REQ_HEADER, SwitchbotDevice

# Command constants for Meter Pro CO2
COMMAND_SET_TIME = f"{REQ_HEADER}0300"


class SwitchbotMeterProCO2(SwitchbotDevice):
    _set_time_command = "570101"
    """Representation of a Switchbot CO₂ Meter Pro (METER_PRO_C)."""

    async def set_time(self, timestamp: int) -> bool:
        """Set the device's internal clock.

        `timestamp` is a Unix epoch (seconds since 1970‑01‑01).
        """
        ts_hex = timestamp.to_bytes(4, "big").hex()
        command = f"{COMMAND_SET_TIME}{ts_hex}"
        result = await self._send_command(command)
        # Verify the command result; raise on failure to match test expectations.
        if not self._check_command_result(result, 0, {1}):
            # Import locally to avoid circular import issues.
            from .device import SwitchbotOperationError

            raise SwitchbotOperationError(
                f"{self.name}: Setting time failed (result={result.hex() if result else 'None'})"
            )
        return True

    async def send_command(self, key: str, retry: int | None = None) -> bytes | None:
        result = await self._send_command(key, retry)
        # Verify the command result; raise on failure to match test expectations.
        if not self._check_command_result(result, 0, {1}):
            # Import locally to avoid circular import issues.
            from .device import SwitchbotOperationError

            raise SwitchbotOperationError(
                f"{self.name}: Setting time failed (result={result.hex() if result else 'None'})"
            )
        return result