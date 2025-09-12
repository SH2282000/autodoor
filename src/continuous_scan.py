import asyncio
import signal
import time

from bleak import BleakScanner


def is_approaching(signal_strength, window_size=10, threshold=10):
    """
    Returns True if approaching, False if moving away, None if stable or not enough data.
    threshold: minimum RSSI difference to consider as movement (default: 3 dBm)
    """
    recent_values = list(signal_strength.values())[-window_size:]

    if len(recent_values) < 2:
        return None

    # Compare first half vs second half of the window
    mid = len(recent_values) // 2
    first_half_avg = sum(recent_values[:mid]) / mid
    second_half_avg = sum(recent_values[mid:]) / (len(recent_values) - mid)

    difference = second_half_avg - first_half_avg

    # If difference is too small, signal is stable
    if abs(difference) < threshold:
        return None

    # Higher RSSI (less negative) = closer
    return difference > 0


async def continuous_scan(address: str, name: str):
    """Continuously scan for BLE devices with real-time callbacks."""
    ABSENCE_THRESHOLD = 10.0

    last_seen = {}
    signal_strength = {}
    last_seen[address] = time.time()
    signal_strength[time.time()] = -120  # base line

    def device_callback(device, advertisement_data):
        """Handle discovered devices in real-time."""
        if device.name == name:
            current_time = time.time()
            signal_strength[current_time] = advertisement_data.rssi

            # match is_approaching(signal_strength):
            #     case True:
            #         print("approaching...")
            #     case False:
            #         print("leaving...")
            #     case _:
            #         print("Not moving...")

            absence_duration = current_time - last_seen[address]
            if absence_duration > ABSENCE_THRESHOLD:
                print(
                    f"Hello again! absence duration: {absence_duration:.2f}s, current time: {time.strftime('%H:%M:%S', time.localtime(current_time))} RSSI: {advertisement_data.rssi} dBm"
                )

            last_seen[address] = current_time

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
    DEVICE_ADRESS = "C0:2C:5C:8D:37:D8"
    DEVICE_NAME = "sPhone"
    asyncio.run(continuous_scan(DEVICE_ADRESS, DEVICE_NAME))
