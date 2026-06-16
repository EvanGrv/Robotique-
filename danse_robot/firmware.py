from microbit import *
import music
import utime


ADDR = 0x10
FORWARD = 1
BACKWARD = 2
OBSTACLE_CM = 20

KP, KI, KD = 0.8, 0, 0
MAX_SPEED = 180
DANCE_SPEED = 120
TURN_SPEED = 130
BACK_SPEED = 100
WHEELIE_SPEED = 255

position_ticks = 0
previous_left = 0
previous_right = 0
integral = 0
previous_error = 0


def write_motors(left_direction, left_speed, right_direction, right_speed):
    i2c.write(
        ADDR,
        bytes([0, left_direction, left_speed, right_direction, right_speed]),
    )


def stop():
    write_motors(0, 0, 0, 0)


def get_distance_cm():
    pin8.write_digital(0)
    utime.sleep_us(2)
    pin8.write_digital(1)
    utime.sleep_us(10)
    pin8.write_digital(0)

    timeout = 30000
    t0 = utime.ticks_us()
    while pin12.read_digital() == 0:
        if utime.ticks_diff(utime.ticks_us(), t0) > timeout:
            return 999

    start = utime.ticks_us()
    while pin12.read_digital() == 1:
        if utime.ticks_diff(utime.ticks_us(), start) > timeout:
            return 999

    duration_us = utime.ticks_diff(utime.ticks_us(), start)
    return duration_us * 0.0343 / 2


def read_register(register):
    i2c.write(ADDR, bytes([register]))
    return i2c.read(ADDR, 4)


def coders():
    data = read_register(4)
    return (data[0] << 8) | data[1], (data[2] << 8) | data[3]


def direction(value):
    return 1 if value == 1 else -1 if value == 2 else 0


def reset_position():
    global position_ticks, previous_left, previous_right
    global integral, previous_error
    stop()
    i2c.write(ADDR, bytes([4, 0, 0, 0]))
    sleep(20)
    previous_left, previous_right = coders()
    position_ticks = integral = previous_error = 0


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


def avoid_obstacle():
    stop()
    display.show(Image.NO)
    music.pitch(220, 120, wait=False)
    sleep(150)
    write_motors(BACKWARD, BACK_SPEED, BACKWARD, BACK_SPEED)
    display.show(Image.ARROW_S)
    sleep(350)
    write_motors(BACKWARD, TURN_SPEED, FORWARD, TURN_SPEED)
    display.show(Image.ARROW_E)
    sleep(450)
    stop()
    reset_position()


def obstacle():
    if get_distance_cm() < OBSTACLE_CM:
        avoid_obstacle()
        return True
    return False


def pid_move(target_ticks, image, tone):
    global integral, previous_error
    update_position()
    error = target_ticks - position_ticks
    integral += error * 0.01
    derivative = (error - previous_error) / 0.01
    previous_error = error
    command = KP * error + KI * integral + KD * derivative
    speed = min(MAX_SPEED, int(abs(command)))
    direct = FORWARD if command > 0 else BACKWARD if command < 0 else 0
    display.show(image)
    music.pitch(tone, 80, wait=False)
    write_motors(direct, speed, direct, speed)


def pid_segment(target_ticks, duration, image, tone):
    reset_position()
    start = running_time()
    while running_time() - start < duration:
        if obstacle():
            return
        pid_move(target_ticks, image, tone)
        sleep(10)
    stop()


def timed_move(left_direction, left_speed, right_direction, right_speed, duration, image, tone):
    start = running_time()
    display.show(image)
    music.pitch(tone, 100, wait=False)
    write_motors(left_direction, left_speed, right_direction, right_speed)
    while running_time() - start < duration:
        if obstacle():
            return
        sleep(20)
    stop()


def wheelie_test():
    stop()
    display.show(Image.DIAMOND)
    music.pitch(988, 100, wait=False)
    sleep(250)
    write_motors(FORWARD, WHEELIE_SPEED, FORWARD, WHEELIE_SPEED)
    sleep(180)
    stop()
    sleep(250)


def dance_cycle():
    pid_segment(140, 600, Image.ARROW_N, 523)
    timed_move(BACKWARD, TURN_SPEED, FORWARD, TURN_SPEED, 450, Image.ARROW_E, 659)
    pid_segment(100, 500, Image.ARROW_N, 784)
    timed_move(FORWARD, TURN_SPEED, BACKWARD, TURN_SPEED, 450, Image.ARROW_W, 659)
    timed_move(BACKWARD, DANCE_SPEED, BACKWARD, DANCE_SPEED, 350, Image.ARROW_S, 523)
    wheelie_test()


display.show(Image.NO)
while ADDR not in i2c.scan():
    sleep(100)

reset_position()
display.show(Image.HAPPY)
music.play(["C4:1", "E4:1", "G4:1"], wait=True)

while True:
    if button_b.was_pressed():
        stop()
        display.show(Image.SQUARE_SMALL)
        while not button_a.was_pressed():
            sleep(20)
        reset_position()
    dance_cycle()
