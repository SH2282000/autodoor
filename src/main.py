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
PHONE_BT_ADDRESS = "XX:XX:XX:XX:XX:XX"  # Replace with your phone's BT address
SCAN_INTERVAL = 2.0  # Seconds between scans
DISCONNECT_THRESHOLD = 10.0  # Seconds to consider device "away"


class BluetoothDoorController:
    def __init__(self, target_address):
        self.target_address = target_address.lower()
        self.last_seen = None
        self.was_connected = False
        self.running = True

        # Initialize pigpio with error checking
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError(
                "Failed to connect to pigpio daemon. Run 'sudo pigpiod' first."
            )

        # Set pin modes
        self.pi.set_mode(IN1, pigpio.OUTPUT)
        self.pi.set_mode(IN2, pigpio.OUTPUT)
        self.pi.set_mode(ENA, pigpio.OUTPUT)

        # Initialize pins to safe state
        self.pi.write(IN1, 0)
        self.pi.write(IN2, 0)
        self.pi.set_PWM_dutycycle(ENA, 0)

        print("🔧 GPIO initialized successfully")

    def motor_control(self, speed, direction):
        """Control motor with speed (0-255) and direction"""
        print(f"🔧 Motor command: {direction} at speed {speed}")

        # Always stop first for safety
        self.pi.write(IN1, 0)
        self.pi.write(IN2, 0)
        self.pi.set_PWM_dutycycle(ENA, 0)
        time.sleep(0.1)  # Brief pause for relay switching

        if direction == "forward":
            self.pi.write(IN1, 1)
            self.pi.write(IN2, 0)
            self.pi.set_PWM_dutycycle(ENA, speed)
            print(
                f"✅ Forward: IN1={self.pi.read(IN1)}, IN2={self.pi.read(IN2)}, PWM={speed}"
            )
        elif direction == "reverse":
            self.pi.write(IN1, 0)
            self.pi.write(IN2, 1)
            self.pi.set_PWM_dutycycle(ENA, speed)
            print(
                f"✅ Reverse: IN1={self.pi.read(IN1)}, IN2={self.pi.read(IN2)}, PWM={speed}"
            )
        else:  # stop
            print("✅ Stop: All pins LOW")

    async def door_sequence(self):
        """Execute door handle sequence"""
        print("🚪 Executing door sequence...")

        try:
            # Forward stroke
            print("Phase 1: Forward stroke")
            self.motor_control(255, "forward")
            await asyncio.sleep(5)

            # Brief pause
            print("Phase 2: Stopping")
            self.motor_control(0, "stop")
            await asyncio.sleep(0.5)

            # Return stroke
            print("Phase 3: Reverse stroke")
            self.motor_control(255, "reverse")
            await asyncio.sleep(6)

            # Final stop
            print("Phase 4: Final stop")
            self.motor_control(0, "stop")
            print("✅ Door sequence completed")

        except Exception as e:
            print(f"❌ Error during sequence: {e}")
            self.motor_control(0, "stop")  # Emergency stop

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
        self.pi.stop()


async def main():
    try:
        controller = BluetoothDoorController(PHONE_BT_ADDRESS)

        def signal_handler(signum, frame):
            controller.cleanup()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        await controller.monitor_connection()

    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        if "controller" in locals():
            controller.cleanup()

if __name__ == "__main__":
    # Ensure pigpio daemon is running
    import subprocess

    try:
        subprocess.run(["sudo", "pigpiod"], check=False, capture_output=True)
    except:
        pass

    asyncio.run(main())