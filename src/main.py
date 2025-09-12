import asyncio
import signal
import time

import pigpio
from bleak import BleakScanner

# Pin definitions
ENA = 18  # Hardware PWM for speed control
IN1 = 17  # Direction pin 1
IN2 = 27  # Direction pin 2

# Initialize pigpio
pi = pigpio.pi()


def motor_control(speed, direction):
    """
    speed: 0-255 (pigpio uses 0-255 range)
    direction: 'forward', 'reverse', or 'stop'
    """
    if direction == "forward":
        pi.write(IN1, 1)  # GPIO 17 HIGH
        pi.write(IN2, 0)  # GPIO 27 LOW
        pi.set_PWM_dutycycle(ENA, speed)
    elif direction == "reverse":
        pi.write(IN1, 0)  # GPIO 17 LOW
        pi.write(IN2, 1)  # GPIO 27 HIGH
        pi.set_PWM_dutycycle(ENA, speed)
    else:  # stop
        pi.write(IN1, 0)
        pi.write(IN2, 0)
        pi.set_PWM_dutycycle(ENA, 0)


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


def cleanup_signal_strength(
    signal_strength, cleanup_interval=60.0, cleanup_size=50
):
    """
    Clean up old signal strength data to prevent exponential growth.

    Args:
        signal_strength: Dictionary containing signal strength data
        cleanup_interval: Time in seconds to keep data (default: 60.0)
        cleanup_size: Maximum number of entries per device (default: 50)
    """
    current_time = time.time()

    # Remove old entries based on time
    for addr in list(signal_strength.keys()):
        if isinstance(signal_strength[addr], dict):
            signal_strength[addr] = {
                timestamp: rssi
                for timestamp, rssi in signal_strength[addr].items()
                if current_time - timestamp <= cleanup_interval
            }

            # If still too many entries, keep only the most recent ones
            if len(signal_strength[addr]) > cleanup_size:
                sorted_items = sorted(signal_strength[addr].items())
                signal_strength[addr] = dict(sorted_items[-cleanup_size:])

            # Remove device entry if no recent data
            if not signal_strength[addr]:
                del signal_strength[addr]


def recognize_device(address, signal_strength, threshold=-30):
    """
    Returns True if the signal strength indicates a recognized device is nearby.
    threshold: RSSI value to consider as recognized (default: -30 dBm)
    """
    recent_values = list(signal_strength[address].values())[-5:]

    if not recent_values:
        return False

    # If any recent value is above the threshold, consider it recognized
    return any(rssi >= threshold for rssi in recent_values)


async def continuous_scan(addresses: list[str], name: str):
    """Continuously scan for BLE devices with real-time callbacks."""
    ABSENCE_THRESHOLD = 10.0

    last_seen = {}
    signal_strength = {}
    for address in addresses:
        last_seen[address] = time.time()
        signal_strength[address] = {time.time(): -120}  # base line

    def device_callback(device, advertisement_data):
        """Handle discovered devices in real-time."""
        if not device.name:
            return

        if device.address in addresses:
            # print(
            #     f"Discovered target device: {device.name}, Address: {device.address}, RSSI: {advertisement_data.rssi} dBm"
            # )
            current_time = time.time()

            # match is_approaching(signal_strength):
            #     case True:
            #         print("approaching...")
            #     case False:
            #         print("leaving...")
            #     case _:
            #         print("Not moving...")

            absence_duration = current_time - last_seen[device.address]
            if absence_duration > ABSENCE_THRESHOLD:
                print(
                    f"Hello again! absence duration: {absence_duration:.2f}s, current time: {time.strftime('%H:%M:%S', time.localtime(current_time))} RSSI: {advertisement_data.rssi} dBm"
                )
                motor_control(200, "forward")  # ~78% speed forward (200/255)
                time.sleep(4)
                motor_control(200, "reverse")  # ~78% speed reverse (200/255)
                time.sleep(4)

                motor_control(0, "stop")  # Stop motor
                pi.stop()

            last_seen[device.address] = current_time

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
    MAIN_DEVICE_ADRESS = "4D57E341-8AFC-E894-373D-E0FDF9275E1F"
    WATCH_DEVICE_ADRESS = "63A5FCD8-4F7D-A5DC-4461-FA7137452DCE"
    MAIN_DEVICE_NAME = "sPhone"

    addresses = [
        MAIN_DEVICE_ADRESS,  # sPhone
        WATCH_DEVICE_ADRESS,  # sWatch
    ]
    asyncio.run(continuous_scan(addresses, MAIN_DEVICE_NAME))
