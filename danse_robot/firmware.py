from microbit import i2c, pin8, pin12, sleep, display, Image
import utime


MAQUEEN_ADDR = 0x10
FORWARD = 1
SPEED = 150
OBSTACLE_CM = 20


def write_motors(left_direction, left_speed, right_direction, right_speed):
    i2c.write(
        MAQUEEN_ADDR,
        bytes([0x00, left_direction, left_speed, right_direction, right_speed]),
    )


def go_forward():
    write_motors(FORWARD, SPEED, FORWARD, SPEED)


def stop():
    write_motors(FORWARD, 0, FORWARD, 0)


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


display.show(Image.ARROW_N)

while True:
    if get_distance_cm() < OBSTACLE_CM:
        stop()
        display.show(Image.NO)
    else:
        go_forward()
        display.show(Image.ARROW_N)
    sleep(100)
