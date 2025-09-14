import asyncio
import signal
import time
from datetime import datetime, timedelta

import pigpio
from bleak import BleakScanner

# Pin definitions
ENA = 18  # Hardware PWM for speed control
IN1 = 17  # Direction pin 1
IN2 = 27  # Direction pin 2

# Configuration
PHONE_BT_ADDRESS = "4D57E341-8AFC-E894-373D-E0FDF9275E1F"  # Replace with your phone's BT address
SCAN_INTERVAL = 2.0  # Seconds between scans
DISCONNECT_THRESHOLD = 10.0  # Seconds to consider device "away"

# Initialize pigpio
pi = pigpio.pi()

class BluetoothDoorController:
    def __init__(self, target_address):
        self.target_address = target_address.lower()
        self.last_seen = None
        self.was_connected = False
        self.running = True

    def motor_control(self, speed, direction):
        """Control motor with speed (0-255) and direction"""
        if direction == "forward":
            pi.write(IN1, 1)
            pi.write(IN2, 0)
            pi.set_PWM_dutycycle(ENA, speed)
        elif direction == "reverse":
            pi.write(IN1, 0)
            pi.write(IN2, 1)
            pi.set_PWM_dutycycle(ENA, speed)
        else:  # stop
            pi.write(IN1, 0)
            pi.write(IN2, 0)
            pi.set_PWM_dutycycle(ENA, 0)

    async def door_sequence(self):
        """Execute door handle sequence"""
        print("🚪 Executing door sequence...")

        # Forward stroke
        self.motor_control(255, "forward")
        await asyncio.sleep(5)

        # Brief pause
        self.motor_control(0, "stop")
        await asyncio.sleep(0.5)

        # Return stroke
        self.motor_control(255, "reverse")
        await asyncio.sleep(6)

        # Stop
        self.motor_control(0, "stop")
        print("✅ Door sequence completed")

    async def scan_for_device(self):
        """Scan for the target Bluetooth device"""
        try:
            devices = await BleakScanner.discover(timeout=SCAN_INTERVAL)
            for device in devices:
                if device.address.lower() == self.target_address:
                    return True
            return False
        except Exception as e:
            print(f"⚠️ Scan error: {e}")
            return False

    async def monitor_connection(self):
        """Main monitoring loop"""
        print(f"🔍 Monitoring for device: {self.target_address}")

        while self.running:
            device_found = await self.scan_for_device()
            current_time = datetime.now()

            if device_found:
                if not self.was_connected:
                    # Device reconnected after being away
                    if self.last_seen:
                        away_duration = current_time - self.last_seen
                        print(
                            f"📱 Device reconnected after {away_duration.total_seconds():.1f} seconds away"
                        )
                    else:
                        print("📱 Device detected for the first time")

                    await self.door_sequence()
                    self.was_connected = True

                self.last_seen = current_time

            else:
                if self.was_connected and self.last_seen:
                    # Check if device has been away long enough
                    time_since_seen = current_time - self.last_seen
                    if time_since_seen.total_seconds() > DISCONNECT_THRESHOLD:
                        print(
                            f"📵 Device disconnected (away for {time_since_seen.total_seconds():.1f}s)"
                        )
                        self.was_connected = False

            await asyncio.sleep(SCAN_INTERVAL)

    def cleanup(self):
        """Clean shutdown"""
        print("\n🛑 Shutting down...")
        self.running = False
        self.motor_control(0, "stop")
        pi.stop()

async def main():
    controller = BluetoothDoorController(PHONE_BT_ADDRESS)

    # Setup signal handlers for clean shutdown
    def signal_handler(signum, frame):
        controller.cleanup()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await controller.monitor_connection()
    except KeyboardInterrupt:
        pass
    finally:
        controller.cleanup()

if __name__ == "__main__":
    asyncio.run(main())