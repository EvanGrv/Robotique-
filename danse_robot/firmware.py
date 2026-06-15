from microbit import *
import music
import utime


ADDR = 0x10
FORWARD = 1
BACKWARD = 2
OBSTACLE_CM = 20

DANCE_SPEED = 100
TURN_SPEED = 110
AVOID_SPEED = 100
WHEELIE_SPEED = 180
WHEELIE_MAX_MS = 700
WHEELIE_TILT_LIMIT = 650


def motors(left_direction, left_speed, right_direction, right_speed):
    i2c.write(
        ADDR,
        bytes([0, left_direction, left_speed, right_direction, right_speed]),
    )


def stop():
    motors(0, 0, 0, 0)


def distance_cm():
    pin8.write_digital(0)
    utime.sleep_us(2)
    pin8.write_digital(1)
    utime.sleep_us(10)
    pin8.write_digital(0)

    started = utime.ticks_us()
    while pin12.read_digital() == 0:
        if utime.ticks_diff(utime.ticks_us(), started) > 30000:
            return 999

    echo = utime.ticks_us()
    while pin12.read_digital() == 1:
        if utime.ticks_diff(utime.ticks_us(), echo) > 30000:
            return 999

    return utime.ticks_diff(utime.ticks_us(), echo) * 0.0343 / 2


def note(frequency):
    music.pitch(frequency, 120, wait=False)


def move(left_direction, left_speed, right_direction, right_speed, image, tone):
    if distance_cm() < OBSTACLE_CM:
        avoid_obstacle()
        return
    display.show(image)
    note(tone)
    motors(left_direction, left_speed, right_direction, right_speed)


def avoid_obstacle():
    stop()
    display.show(Image.NO)
    note(220)
    sleep(150)
    motors(BACKWARD, AVOID_SPEED, BACKWARD, AVOID_SPEED)
    display.show(Image.ARROW_S)
    sleep(350)
    motors(BACKWARD, TURN_SPEED, FORWARD, TURN_SPEED)
    display.show(Image.ARROW_E)
    sleep(450)
    stop()


def wheelie():
    start = running_time()
    display.show(Image.DIAMOND)
    note(784)
    motors(FORWARD, WHEELIE_SPEED, FORWARD, WHEELIE_SPEED)

    while running_time() - start < WHEELIE_MAX_MS:
        if distance_cm() < OBSTACLE_CM or abs(accelerometer.get_z()) > WHEELIE_TILT_LIMIT:
            break
        sleep(10)

    stop()
    sleep(250)


STEPS = (
    (FORWARD, DANCE_SPEED, FORWARD, DANCE_SPEED, Image.ARROW_N, 523, 450),
    (BACKWARD, TURN_SPEED, FORWARD, TURN_SPEED, Image.ARROW_E, 659, 400),
    (FORWARD, TURN_SPEED, BACKWARD, TURN_SPEED, Image.ARROW_W, 784, 400),
    (BACKWARD, DANCE_SPEED, BACKWARD, DANCE_SPEED, Image.ARROW_S, 659, 350),
)


display.show(Image.NO)
while ADDR not in i2c.scan():
    sleep(100)

stop()
display.show(Image.HAPPY)
music.play(["C4:2", "E4:2", "G4:2"], wait=True)

step = 0
step_started = running_time()
move(*STEPS[step][0:6])

while True:
    if button_b.was_pressed():
        stop()
        display.show(Image.SQUARE_SMALL)
        while not button_a.was_pressed():
            sleep(20)
        step_started = running_time()

    if distance_cm() < OBSTACLE_CM:
        avoid_obstacle()
        step_started = running_time()
        move(*STEPS[step][0:6])

    if running_time() - step_started >= STEPS[step][6]:
        stop()
        step += 1
        if step >= len(STEPS):
            wheelie()
            step = 0
        step_started = running_time()
        move(*STEPS[step][0:6])

    sleep(20)
