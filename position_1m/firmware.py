from microbit import *


ADDRESS = 0x10
TARGET_M = 1.0
TICKS_PER_METER = 80 / (2 * 3.14159265 * 0.0215)
KP, KI, KD = 200, 0, 0

IDLE, CALIBRATION, MOVING = 0, 1, 2
state = IDLE
combo_pressed = False
ticks = 0
previous_left = 0
previous_right = 0
integral = 0
previous_error = 0
last_report = running_time()


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


def motor(command):
    speed = min(80, max(20, int(abs(command)))) if command else 0
    direction = 1 if command > 0 else 2 if command < 0 else 0
    i2c.write(ADDRESS, bytes([0x00, direction, speed, direction, speed]))


def reset_position():
    global ticks, previous_left, previous_right, integral, previous_error
    motor(0)
    i2c.write(ADDRESS, bytes([0x04, 0, 0, 0]))
    sleep(20)
    previous_left, previous_right = coders()
    ticks = integral = previous_error = 0


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
    return left, right, left_direction, right_direction


def move_to(target):
    global state, integral, previous_error
    error = target - ticks / TICKS_PER_METER
    integral += error * 0.01
    derivative = (error - previous_error) / 0.01
    previous_error = error

    if abs(error) < 0.005:
        motor(0)
        state = IDLE
        display.show(Image.TARGET)
    else:
        command = KP * error + KI * integral + KD * derivative
        motor(command)
        display.show(Image.ARROW_N if command > 0 else Image.ARROW_S)


def start_calibration():
    global state
    reset_position()
    state = CALIBRATION
    display.show("C")
    print("STATE CALIBRATION")


def finish_calibration():
    global state, TICKS_PER_METER
    left, right = coders()
    measured_ticks = (left + right) / 2
    if measured_ticks > 100:
        TICKS_PER_METER = measured_ticks
        display.show(Image.YES)
        print("CALIBRATED ticks_per_meter={}".format(TICKS_PER_METER))
    else:
        display.show(Image.NO)
        print("CALIBRATION_REJECTED ticks={}".format(measured_ticks))
    reset_position()
    state = IDLE


def start_move():
    global state, integral, previous_error
    integral = previous_error = 0
    state = MOVING
    print("STATE MOVING target_m={} ticks_per_meter={}".format(
        TARGET_M, TICKS_PER_METER
    ))


while ADDRESS not in i2c.scan():
    display.show(Image.NO)
    sleep(100)

reset_position()
display.show("R")
print("STATE READY ticks_per_meter={}".format(TICKS_PER_METER))

while True:
    both = button_a.is_pressed() and button_b.is_pressed()

    if both and not combo_pressed:
        combo_pressed = True
        start_calibration()
    elif not both and combo_pressed:
        button_a.was_pressed()
        button_b.was_pressed()
        combo_pressed = False
    elif not combo_pressed:
        if button_b.was_pressed():
            if state == CALIBRATION:
                finish_calibration()
            else:
                reset_position()
                state = IDLE
                display.show("R")
                print("STATE RESET")
        elif button_a.was_pressed() and state == IDLE:
            start_move()

    left, right, left_direction, right_direction = update_position()
    if state == MOVING:
        move_to(TARGET_M)

    if running_time() - last_report > 500:
        last_report = running_time()
        print("READ state={} raw={}:{} dir={}:{} ticks={} position={}".format(
            state, left, right, left_direction, right_direction, ticks,
            ticks / TICKS_PER_METER,
        ))

    sleep(10)
