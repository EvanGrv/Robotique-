from microbit import *


MAQUEEN_ADDRESS = 0x10
DEFAULT_SPEED = 80
WATCHDOG_MS = 700

speed = DEFAULT_SPEED
last_motion = running_time()
moving = False
input_buffer = b""
connected = False


def write_motors(left_direction, left_speed, right_direction, right_speed):
    global connected
    try:
        i2c.write(
            MAQUEEN_ADDRESS,
            bytes([0x00, left_direction, left_speed, right_direction, right_speed]),
        )
        connected = True
        return True
    except OSError as error:
        print("ERROR Maqueen connection:", error)
        display.show(Image.NO)
        connected = False
        return False


def stop():
    global moving
    write_motors(0, 0, 0, 0)
    moving = False
    display.show(Image.SQUARE_SMALL)


def move(left_direction, right_direction):
    global last_motion, moving
    if not write_motors(left_direction, speed, right_direction, speed):
        moving = False
        return
    last_motion = running_time()
    moving = True


def status():
    global connected
    try:
        i2c.write(MAQUEEN_ADDRESS, bytes([0x00]))
        motors = list(i2c.read(MAQUEEN_ADDRESS, 4))
        connected = True
        print("STATUS speed={} motors={}".format(speed, motors))
    except OSError as error:
        connected = False
        print("STATUS Maqueen unavailable:", error)


def handle(command):
    global speed

    command = command.strip().lower()
    if command in ("forward", "f"):
        move(1, 1)
        display.show(Image.ARROW_N)
    elif command in ("back", "b"):
        move(2, 2)
        display.show(Image.ARROW_S)
    elif command in ("left", "l"):
        move(2, 1)
        display.show(Image.ARROW_W)
    elif command in ("right", "r"):
        move(1, 2)
        display.show(Image.ARROW_E)
    elif command in ("stop", "x", ""):
        stop()
    elif command == "status":
        status()
    elif command == "start":
        stop()
        print("READY")
    elif command == "reset":
        speed = DEFAULT_SPEED
        stop()
        print("RESET")
    elif command.startswith("speed "):
        speed = max(0, min(240, int(command.split()[1])))
        print("SPEED", speed)
    else:
        print("UNKNOWN", command)
        return

    print("OK", command)


try:
    while True:
        if not connected and MAQUEEN_ADDRESS in i2c.scan():
            connected = True
            stop()
            print("READY Maqueen remote, speed={}".format(speed))
        elif not connected:
            display.show(Image.NO)

        if uart.any():
            input_buffer += uart.read()
            while b"\n" in input_buffer:
                line, input_buffer = input_buffer.split(b"\n", 1)
                try:
                    handle(line.decode("utf-8"))
                except Exception as error:
                    stop()
                    print("ERROR", error)

        if moving and running_time() - last_motion > WATCHDOG_MS:
            stop()
            print("WATCHDOG stop")

        sleep(10)
finally:
    try:
        stop()
    except OSError:
        pass
