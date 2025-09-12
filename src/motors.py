import sys
import time

import pigpio

# Pin definitions
ENA = 18    # Hardware PWM for speed control
IN1 = 17    # Direction pin 1
IN2 = 27    # Direction pin 2

# Initialize pigpio
pi = pigpio.pi()

def motor_control(speed, direction):
    """
    speed: 0-255 (pigpio uses 0-255 range)
    direction: 'forward', 'reverse', or 'stop'
    """
    if direction == 'forward':
        pi.write(IN1, 1)  # GPIO 17 HIGH
        pi.write(IN2, 0)  # GPIO 27 LOW
        pi.set_PWM_dutycycle(ENA, speed)
    elif direction == 'reverse':
        pi.write(IN1, 0)  # GPIO 17 LOW
        pi.write(IN2, 1)  # GPIO 27 HIGH
        pi.set_PWM_dutycycle(ENA, speed)
    else:  # stop
        pi.write(IN1, 0)
        pi.write(IN2, 0)
        pi.set_PWM_dutycycle(ENA, 0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python motors.py <1|0>")
        sys.exit(1)

    direction_arg = sys.argv[1]

    if direction_arg not in ["1", "0"]:
        print("Direction must be '1' (forward) or '0' (backward)")
        sys.exit(1)

    direction = "forward" if direction_arg == "1" else "reverse"

    motor_control(200, direction)
    time.sleep(1)
    motor_control(0, "stop")

    # Cleanup
    pi.stop()
