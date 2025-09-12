import asyncio
import signal

from bleak import BleakScanner


async def continuous_scan():
    """Continuously scan for BLE devices with real-time callbacks."""

    def device_callback(device, advertisement_data):
        """Handle discovered devices in real-time."""
        if not device.name:
            return

        print(
            f"Discovered target device: {device.name}, Address: {device.address}, RSSI: {advertisement_data.rssi} dBm"
        )

    # Create stop event for graceful shutdown
    stop_event = asyncio.Event()

    # Set up signal handler for Ctrl+C
    def signal_handler():
        print("\nStopping scan...")
        stop_event.set()

    # Register signal handler
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    async with BleakScanner(detection_callback=device_callback) as scanner:
        print("Scanning for BLE devices... Press Ctrl+C to stop")
        await stop_event.wait()


if __name__ == "__main__":
    asyncio.run(continuous_scan())
