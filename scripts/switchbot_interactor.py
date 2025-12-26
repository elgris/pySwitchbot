
import asyncio
import logging
import time
import sys
from typing import cast

from bleak import BleakScanner
from switchbot import (
    GetSwitchbotDevices,
    SwitchbotModel,
    Switchbot,
    SwitchbotCurtain,
    SwitchbotPlugMini,
    SwitchbotLock,
    SwitchbotBlindTilt,
    SwitchbotDevice,
    SwitchbotMeterProCO2,
)
from switchbot.models import SwitchBotAdvertisement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SwitchbotInteractor")

# Mapping from SwitchbotModel to specific Device Class
# This allows us to instantiate the correct class for a given device type
DEVICE_CLASS_MAP = {
    SwitchbotModel.BOT: Switchbot,
    SwitchbotModel.CURTAIN: SwitchbotCurtain,
    SwitchbotModel.PLUG_MINI: SwitchbotPlugMini,
    SwitchbotModel.PLUG_MINI_EU: SwitchbotPlugMini,
    SwitchbotModel.LOCK: SwitchbotLock,
    SwitchbotModel.LOCK_PRO: SwitchbotLock, 
    SwitchbotModel.BLIND_TILT: SwitchbotBlindTilt,
    SwitchbotModel.METER_PRO_C: SwitchbotMeterProCO2,
    # Add other mappings as identified in the library
}

async def scan_for_devices(scan_duration=5):
    """Scan for Switchbot devices."""
    logger.info("Scanning for Switchbot devices...")
    scanner = GetSwitchbotDevices()
    
    # We can use the discover method which returns a dict of address -> advertisement
    devices = await scanner.discover(scan_timeout=scan_duration)
    
    logger.info(f"Found {len(devices)} devices.")
    return devices

async def interact_with_device(address: str, adv: SwitchBotAdvertisement):
    """Connect to a device and interact."""
    model = adv.data.get("model")
    modelName = adv.data.get("modelName") # sometimes available
    
    logger.info(f"--- Interacting with {address} ({model})({modelName}) ---")
    for key, value in adv.data.items():
        logger.info(f"adv.data[{key!r}] = {value!r}")
    
    # Identify the correct class
    device_class = DEVICE_CLASS_MAP.get(modelName, SwitchbotDevice)
    logger.info(f"Identified device class: {device_class.__name__}")
    
    # Create device instance
    # Note: SwitchbotDevice constructor takes (device: BLEDevice, password=None, interface=...)
    # We should pass the BLEDevice from the advertisement
    device = cast(SwitchbotMeterProCO2, device_class(device=adv.device))
    cmds = [
        "570f690506", 
        "570f6901", 
        "570f680506800f1000",
        # "570f68050680000000"
        # "570005030d0000000069542B8B1e" # 57:00:05:03:0d:00:00:00:00:69:52:91:10:00
        # "570f68050580"
    ]
    # 69541d3c - Tuesday, December 30, 2025 6:43:08 PM (18:43:08) GMT (19:43 local time)
    # "57000503000000000069541d3c00" - 6:43 (GMT-12)
    # "57000503070000000069541d3c00" - 13:43 (GMT-5)
    # "570005030c0000000069541d3c00" - 18:43 (GMT+0)
    # "57000503160000000069541d3c00" - 4:43 (GMT+10)
    # "57000503180000000069541d3c00" - 6:43 (GMT+12)
    # "57000503190000000069541d3c00" - 6:43 (GMT+13)
    # 57000503110000000069542a991e - 00:40 (GMT+5.5, India)
    


    # Findings:
    # - The API corrects time from the current "true time" (000000 sets the time to my current timezone).
    # Perhaps the starting point is the "firmware time" that you could get with other commands that it sends before.
    # - 57:0f:68:05:06 is the command code, perhaps used for both requesting and setting the time.
    # - code 80 - minus to the current time, code 00 - plus
    # - it uses all 3 bytes.
    # Need a script that calcualtes 
    # b1b1-b2b2: b1b1 * 4 - minutes ...
    # 0f00: 20:35 -> 19:31 (1235 -> 1171, diff: 64)
    # ff00: 20:36 -> 2:28 (1236 -> 148, diff: 1088)
    # 1000: 20:40 -> 19:32 (1240 -> 1172, diff: 68)

    # Next steps:
    # - turn the device off and see how setting the "zero" changes it after being offline for a while.
    #   oddly enough, the time didn't change at all
    try:
        logger.info("Connecting and updating status...")
        # connection happens implicitly during update() or sending commands
        await device.update()
        logger.info("Connection successful.")
        logger.info(f"Device State: {device.data}")
        for cmd in cmds:
            logger.info(f"Sending commd {cmd}")
            result = await device.send_command(cmd)
            logger.info(f"Got result: {result} (hex: {result.hex("-") if isinstance(result, (bytes, bytearray)) else ""})")
            # time.sleep(2)
        
        logger.info("Subscribing to notifications...")
        # Example: if it's a Bot, check if we can get specific info
        if isinstance(device, Switchbot):
            logger.info(f"Bot Mode: {device.get_basic_info()}")
            
    except Exception as e:
        logger.error(f"Failed to interact with {address}: {e}")
    finally:
        logger.info(f"--- Finished with {address} ---\n")

async def main():
    try:
        devices = await scan_for_devices()
        
        if not devices:
            logger.info("No devices found.")
            return

        for address, adv in devices.items():
            logger.info(f"Found device: {address}, Model: {adv.data.get('model')}, RSSI: {adv.rssi}")
            
            # Interact with the device
            await interact_with_device(address, adv)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
