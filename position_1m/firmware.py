from microbit import *


ADDRESS = 0x10
TARGET_M = 1.0
KP, KI, KD = 200, 0, 0

ticks_per_meter = 0
ticks = 0
previous_left = 0
previous_right = 0
integral = 0
previous_error = 0
moving = False


def read(register):
    i2c.write(ADDRESS, bytes([register]))
    return i2c.read(ADDRESS, 4)


def coders():
    data = read(0x04)
    return (data[0] << 8) | data[1], (data[2] << 8) | data[3]


def directions():
    data = read(0x00)
    return data[0], data[2]


def sign(direction):
    return 1 if direction == 1 else -1 if direction == 2 else 0


def reset():
    global ticks, previous_left, previous_right, integral, previous_error, moving
    motor(0)
    i2c.write(ADDRESS, bytes([0x04, 0, 0, 0]))
    sleep(20)
    previous_left, previous_right = coders()
    ticks = integral = previous_error = 0
    moving = False


def update_position():
    global ticks, previous_left, previous_right
    left, right = coders()
    left_direction, right_direction = directions()
    left_delta = (left - previous_left) & 0xFFFF
    right_delta = (right - previous_right) & 0xFFFF
    if left_delta < 100 and right_delta < 100:
        ticks += (
            left_delta * sign(left_direction)
            + right_delta * sign(right_direction)
        ) / 2
    previous_left, previous_right = left, right


def motor(command):
    speed = min(80, max(20, int(abs(command)))) if command else 0
    direction = 1 if command > 0 else 2 if command < 0 else 0
    i2c.write(ADDRESS, bytes([0x00, direction, speed, direction, speed]))


def move_to(target):
    global integral, previous_error, moving
    error = target - ticks / ticks_per_meter
    integral += error * 0.01
    derivative = (error - previous_error) / 0.01
    previous_error = error

    if abs(error) < 0.005:
        motor(0)
        moving = False
    else:
        motor(KP * error + KI * integral + KD * derivative)


def calibrate():
    global ticks_per_meter
    reset()
    display.show("C")
    while button_a.is_pressed() or button_b.is_pressed():
        sleep(10)
    button_a.was_pressed()
    button_b.was_pressed()
    while not button_b.was_pressed():
        sleep(10)
    left, right = coders()
    ticks_per_meter = (left + right) / 2
    reset()
    display.show(Image.YES)


while ADDRESS not in i2c.scan():
    sleep(100)

reset()

while True:
    if button_a.is_pressed() and button_b.is_pressed():
        calibrate()
        sleep(500)
    elif button_a.was_pressed() and ticks_per_meter:
        integral = previous_error = 0
        moving = True
    elif button_b.was_pressed():
        reset()

    update_position()
    if moving:
        move_to(TARGET_M)
    sleep(10)
