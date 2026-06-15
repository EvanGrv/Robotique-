from microbit import *


ADDR = 0x10
KP, KI, KD = 2, 0, 0
MAX_SPEED = 200
TOLERANCE_TICKS = 6

target_ticks = 0
position_ticks = 0
previous_left = 0
previous_right = 0
integral = 0
previous_error = 0
state = 0  # 0: calibration required, 1: calibration, 2: hold 1 m
combo = False
last_direct = -1
last_speed = -1


def read_register(register):
    # Place the Maqueen register cursor before every read.
    i2c.write(ADDR, bytes([register]))
    return i2c.read(ADDR, 4)


def coders():
    data = read_register(4)
    return (data[0] << 8) | data[1], (data[2] << 8) | data[3]


def motor_directions():
    data = read_register(0)
    return data[0], data[2]


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


def reset():
    global position_ticks, previous_left, previous_right
    global integral, previous_error
    motor(0)
    i2c.write(ADDR, bytes([4, 0, 0, 0]))
    sleep(20)
    previous_left, previous_right = coders()
    position_ticks = integral = previous_error = 0


def update_position():
    global position_ticks, previous_left, previous_right
    left, right = coders()
    left_direction, right_direction = motor_directions()
    delta_left = (left - previous_left) & 0xFFFF
    delta_right = (right - previous_right) & 0xFFFF
    if delta_left < 100 and delta_right < 100:
        position_ticks += (
            delta_left * direction(left_direction)
            + delta_right * direction(right_direction)
        ) / 2
    previous_left, previous_right = left, right


def pid():
    global integral, previous_error
    error_ticks = target_ticks - position_ticks
    integral += error_ticks * 0.01
    derivative = (error_ticks - previous_error) / 0.01
    previous_error = error_ticks

    if abs(error_ticks) <= TOLERANCE_TICKS:
        motor(0)
    else:
        motor(KP * error_ticks + KI * integral + KD * derivative)


while ADDR not in i2c.scan():
    sleep(100)

reset()
display.show("C")

while True:
    both = button_a.is_pressed() and button_b.is_pressed()

    if both and not combo:
        combo = True
        target_ticks = 0
        reset()
        state = 1
        display.show("C")
    elif not both and combo:
        button_a.was_pressed()
        button_b.was_pressed()
        combo = False
    elif not combo and button_b.was_pressed():
        if state == 1:
            update_position()
            left, right = coders()
            target_ticks = (left + right) / 2
            if target_ticks > 100:
                position_ticks = target_ticks
                integral = previous_error = 0
                state = 2
                display.show(Image.YES)
        else:
            motor(0)
    elif not combo and button_a.was_pressed() and target_ticks:
        state = 2

    update_position()
    if state == 2:
        pid()
    sleep(10)
