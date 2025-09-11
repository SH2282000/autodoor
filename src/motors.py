import pigpio
import time

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

# Example usage
motor_control(200, 'forward')   # ~78% speed forward (200/255)
time.sleep(3)
motor_control(128, 'reverse')   # 50% speed reverse
time.sleep(3)
motor_control(0, 'stop')        # Stop motor

# Cleanup
pi.stop()
