from microbit import *


ADDR = 0x10
TARGET_TICKS = 80 / (2 * 3.14159265 * 0.0215)
KP, KI, KD = 2, 0, 0
MAX_SPEED = 200
TOLERANCE_TICKS = 6

position_ticks = 0
previous_left = 0
previous_right = 0
integral = 0
previous_error = 0
running = False
last_direct = -1
last_speed = -1


def read_register(register):
    i2c.write(ADDR, bytes([register]))
    return i2c.read(ADDR, 4)


def coders():
    data = read_register(4)
    return (data[0] << 8) | data[1], (data[2] << 8) | data[3]


def direction(value):
    return 1 if value == 1 else -1 if value == 2 else 0


def motor(command):
    global last_direct, last_speed
    speed = min(MAX_SPEED, int(abs(command))) if command else 0
    direct = 1 if command > 0 else 2 if command < 0 else 0
    if direct == last_direct and speed == last_speed:
        return
    i2c.write(ADDR, bytes([0, direct, speed, direct, speed]))
    last_direct, last_speed = direct, speed


def reset_and_start():
    global position_ticks, previous_left, previous_right
    global integral, previous_error, running
    motor(0)
    i2c.write(ADDR, bytes([4, 0, 0, 0]))
    sleep(20)
    previous_left, previous_right = coders()
    position_ticks = integral = previous_error = 0
    running = True
    display.show(Image.ARROW_N)


def update_position():
    global position_ticks, previous_left, previous_right
    left, right = coders()
    motor_data = read_register(0)
    left_delta = (left - previous_left) & 0xFFFF
    right_delta = (right - previous_right) & 0xFFFF
    if left_delta < 100 and right_delta < 100:
        position_ticks += (
            left_delta * direction(motor_data[0])
            + right_delta * direction(motor_data[2])
        ) / 2
    previous_left, previous_right = left, right


def pid():
    global integral, previous_error
    error = TARGET_TICKS - position_ticks
    integral += error * 0.01
    derivative = (error - previous_error) / 0.01
    previous_error = error

    if abs(error) <= TOLERANCE_TICKS:
        motor(0)
        display.show(Image.TARGET)
    else:
        motor(KP * error + KI * integral + KD * derivative)


display.show(Image.NO)
while ADDR not in i2c.scan():
    sleep(100)

reset_and_start()

while True:
    if button_a.was_pressed():
        reset_and_start()
    if button_b.was_pressed():
        motor(0)
        running = False
        display.show(Image.SQUARE_SMALL)

    update_position()
    if running:
        pid()
    sleep(10)
