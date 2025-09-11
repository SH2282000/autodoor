import signal
import asyncio
import time
from bleak import BleakScanner

async def continuous_scan():
    """Continuously scan for BLE devices with absence/reappearance detection."""
    
    TARGET_ADDRESS = "C0:2C:5C:8D:37:D8"
    ABSENCE_THRESHOLD = 5.0  # seconds - device considered "gone" after this time
        
    def device_callback(device, advertisement_data):
        """Handle discovered devices with absence/reappearance logic."""
        if device.address == TARGET_ADDRESS:
            current_time = time.time()
            last_seen = current_time
            
            if (current_time - last_seen > ABSENCE_THRESHOLD):
                print(f"Hello again! RSSI: {advertisement_data.rssi} dBm")
    
    def signal_handler():
        print("\nStopping scan...")
        stop_event.set()
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)
    
    async with BleakScanner(detection_callback=device_callback) as scanner:
        await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(continuous_scan())
