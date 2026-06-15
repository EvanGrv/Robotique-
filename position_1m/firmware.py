from microbit import *


MAQUEEN_ADDRESS = 0x10

WHEEL_RADIUS_M = 0.0215
TICKS_PER_WHEEL_REVOLUTION = 80
TICKS_PER_METER = TICKS_PER_WHEEL_REVOLUTION / (
    2 * 3.14159265 * WHEEL_RADIUS_M
)

TARGET_M = 1.0
KP = 200
MAX_SPEED = 80
MIN_SPEED = 20
TOLERANCE_M = 0.005
LOOP_DELAY_MS = 10
MAX_DELTA_TICKS = 100

moving = False
combo_latched = False
last_report_time = running_time()

left_previous = 0
right_previous = 0
left_ticks = 0
right_ticks = 0


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def write_register(register, values=()):
    i2c.write(MAQUEEN_ADDRESS, bytes([register] + list(values)))


def read_coders():
    write_register(0x04)
    data = i2c.read(MAQUEEN_ADDRESS, 4)
    left = (data[0] << 8) | data[1]
    right = (data[2] << 8) | data[3]
    return left, right


def read_directions():
    write_register(0x00)
    data = i2c.read(MAQUEEN_ADDRESS, 4)
    return data[0], data[2]


def direction_sign(direction):
    if direction == 1:
        return 1
    if direction == 2:
        return -1
    return 0


def coder_delta(current, previous):
    delta = (current - previous) & 0xFFFF
    if delta > MAX_DELTA_TICKS:
        print("DELTA_IGNORED", delta)
        return 0
    return delta


def update_position():
    global left_previous, right_previous, left_ticks, right_ticks

    left_coder, right_coder = read_coders()
    left_direction, right_direction = read_directions()

    left_delta = coder_delta(left_coder, left_previous)
    right_delta = coder_delta(right_coder, right_previous)

    left_ticks += left_delta * direction_sign(left_direction)
    right_ticks += right_delta * direction_sign(right_direction)

    left_previous = left_coder
    right_previous = right_coder


def position_m():
    average_ticks = (left_ticks + right_ticks) / 2
    return average_ticks / TICKS_PER_METER


def motor_values(command):
    if command == 0:
        return 0, 0

    speed = int(clamp(abs(command), MIN_SPEED, MAX_SPEED))
    if command > 0:
        return 1, speed
    return 2, speed


def motor(command):
    direction, speed = motor_values(command)
    write_register(0x00, (direction, speed, direction, speed))


def stop():
    global moving
    motor(0)
    moving = False
    display.show(Image.SQUARE_SMALL)


def reset_position():
    global left_previous, right_previous, left_ticks, right_ticks

    stop()
    write_register(0x04, (0, 0, 0))
    sleep(20)
    left_previous, right_previous = read_coders()
    left_ticks = 0
    right_ticks = 0
    display.show(Image.YES)
    print("RESET position_m=0 left_ticks=0 right_ticks=0")


def move_to(target_m):
    global moving

    error_m = target_m - position_m()
    if abs(error_m) <= TOLERANCE_M:
        stop()
        display.show(Image.TARGET)
        print("TARGET position_m={}".format(position_m()))
        return

    command = error_m * KP
    motor(command)
    moving = True
    display.show(Image.ARROW_N if command > 0 else Image.ARROW_S)


def report_status():
    left_direction, right_direction = read_directions()
    print(
        "STATUS moving={} position_m={} error_m={} "
        "left_ticks={} right_ticks={} left_dir={} right_dir={}".format(
            moving,
            position_m(),
            TARGET_M - position_m(),
            left_ticks,
            right_ticks,
            left_direction,
            right_direction,
        )
    )


while MAQUEEN_ADDRESS not in i2c.scan():
    display.show(Image.NO)
    sleep(500)

reset_position()
print("READY A=move B=stop AB=reset ticks_per_meter={}".format(TICKS_PER_METER))

try:
    while True:
        both_pressed = button_a.is_pressed() and button_b.is_pressed()

        if both_pressed and not combo_latched:
            combo_latched = True
            reset_position()
        elif not both_pressed and combo_latched:
            button_a.was_pressed()
            button_b.was_pressed()
            combo_latched = False
        elif not combo_latched:
            if button_a.was_pressed():
                moving = True
            if button_b.was_pressed():
                stop()

        update_position()
        if moving:
            move_to(TARGET_M)

        if running_time() - last_report_time >= 1000:
            last_report_time = running_time()
            report_status()

        sleep(LOOP_DELAY_MS)
finally:
    motor(0)
