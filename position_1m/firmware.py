from microbit import *


MAQUEEN_ADDRESS = 0x10
CONFIG_FILE = "position_config.txt"

WHEEL_RADIUS_M = 0.0215
WHEEL_BASE_M = 0.085
ENCODER_COUNTS_PER_REVOLUTION = 80
THEORETICAL_TICKS_PER_METER = (
    ENCODER_COUNTS_PER_REVOLUTION / (2 * 3.14159265 * WHEEL_RADIUS_M)
)

CONTROL_PERIOD_MS = 50
POSITION_TOLERANCE_TICKS = 2
INTEGRAL_LIMIT = 1500
MAX_RUN_TIME_MS = 20000
MAX_OVERSHOOT_TICKS = 30
MAX_DELTA_TICKS = 100
MAX_SPEED = 80
APPROACH_SPEED = 38
APPROACH_ZONE_TICKS = 80
MIN_MOVING_SPEED = 20

IDLE = 0
DISTANCE_SELECT = 1
MANUAL_CALIBRATION = 2
RUNNING_TO_TARGET = 3

config = {
    "ticks_per_meter": 539.0,
    "calibrated": True,
    "calibration_samples": 1,
    "calibration_ticks_total": 539.0,
    "distance_cm": 100,
    "kp_position": 0.3686,
    "ki_position": 0.0,
    "kd_position": 0.58,
    "kp_heading": 0.75,
    "kd_heading": 0.35,
}
CONFIG_KEYS = (
    "ticks_per_meter",
    "calibrated",
    "calibration_samples",
    "calibration_ticks_total",
    "distance_cm",
    "kp_position",
    "ki_position",
    "kd_position",
    "kp_heading",
    "kd_heading",
)

state = IDLE
connected = False
combo_latched = False
target_ticks = 0
position_integral = 0.0
previous_position_error = 0
previous_heading_error = 0
last_control_time = running_time()
last_report_time = running_time()
run_started = 0
left_raw_previous = 0
right_raw_previous = 0
left_position_ticks = 0
right_position_ticks = 0
manual_motion_unknown = False


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def sign(value):
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def load_config():
    try:
        with open(CONFIG_FILE, "r") as config_file:
            for line in config_file.read().split("\n"):
                if not line:
                    continue
                try:
                    key, value = line.strip().split("=", 1)
                    if key not in config:
                        continue
                    if isinstance(config[key], bool):
                        config[key] = value == "True"
                    elif isinstance(config[key], int):
                        config[key] = int(value)
                    else:
                        config[key] = float(value)
                except ValueError:
                    print("CONFIG_LINE_IGNORED", line)
        print("CONFIG_LOADED", config)
    except OSError:
        print("CONFIG_DEFAULT", config)


def save_config():
    try:
        with open(CONFIG_FILE, "w") as config_file:
            for key in CONFIG_KEYS:
                config_file.write("{}={}\n".format(key, config[key]))
        print("CONFIG_SAVED", config)
    except OSError as error:
        print("ERROR saving config:", error)


def write_register(register, values=()):
    i2c.write(MAQUEEN_ADDRESS, bytes([register] + list(values)))


def read_raw_encoders():
    write_register(0x04)
    data = i2c.read(MAQUEEN_ADDRESS, 4)
    return (data[0] << 8) | data[1], (data[2] << 8) | data[3]


def read_motor_directions():
    write_register(0x00)
    data = i2c.read(MAQUEEN_ADDRESS, 4)
    return data[0], data[2]


def direction_sign(direction):
    if direction == 1:
        return 1
    if direction == 2:
        return -1
    return 0


def raw_delta(current, previous):
    delta = (current - previous) & 0xFFFF
    return delta if delta <= MAX_DELTA_TICKS else 0


def reset_position():
    global left_raw_previous, right_raw_previous
    global left_position_ticks, right_position_ticks, manual_motion_unknown
    reset_encoders()
    left_raw_previous, right_raw_previous = read_raw_encoders()
    left_position_ticks = 0
    right_position_ticks = 0
    manual_motion_unknown = False


def update_position():
    global left_raw_previous, right_raw_previous
    global left_position_ticks, right_position_ticks, manual_motion_unknown

    left_raw, right_raw = read_raw_encoders()
    left_direction, right_direction = read_motor_directions()
    left_delta = raw_delta(left_raw, left_raw_previous)
    right_delta = raw_delta(right_raw, right_raw_previous)

    left_sign = direction_sign(left_direction)
    right_sign = direction_sign(right_direction)
    if (left_delta and not left_sign) or (right_delta and not right_sign):
        manual_motion_unknown = True

    left_position_ticks += left_delta * left_sign
    right_position_ticks += right_delta * right_sign
    left_raw_previous = left_raw
    right_raw_previous = right_raw
    return left_position_ticks, right_position_ticks


def reset_encoders():
    write_register(0x04, (0, 0, 0))


def motor_values(command):
    speed = int(clamp(abs(command), 0, 240))
    if not speed:
        return 0, 0
    return (1 if command > 0 else 2), speed


def set_signed_motors(left_command, right_command):
    left_direction, left_speed = motor_values(left_command)
    right_direction, right_speed = motor_values(right_command)
    write_register(
        0x00,
        (left_direction, left_speed, right_direction, right_speed),
    )


def stop_motors():
    write_register(0x00, (0, 0, 0, 0))


def reset_pid(initial_error=0):
    global position_integral, previous_position_error, previous_heading_error
    global last_control_time
    position_integral = 0.0
    previous_position_error = initial_error
    previous_heading_error = 0
    last_control_time = running_time()


def show_distance():
    display.scroll(str(config["distance_cm"]) + "cm", wait=True, loop=False)
    display.show(Image.SQUARE_SMALL)


def enter_idle():
    global state
    stop_motors()
    state = IDLE
    display.show(Image.SQUARE_SMALL)
    print("IDLE A=set_origin_and_hold B=distance AB=calibrate_1m")


def start_run():
    global state, target_ticks, run_started
    stop_motors()
    reset_position()
    target_ticks = int(
        config["ticks_per_meter"] * config["distance_cm"] / 100
    )
    reset_pid(target_ticks)
    run_started = running_time()
    state = RUNNING_TO_TARGET
    display.show(Image.ARROW_N)
    print("RUN origin=0 distance_cm={} target_ticks={}".format(
        config["distance_cm"], target_ticks
    ))


def emergency_stop():
    global state
    stop_motors()
    state = IDLE
    display.show(Image.NO)
    print("EMERGENCY_STOP")


def finish_manual_calibration():
    global state
    left_raw, right_raw = read_raw_encoders()
    left, right = left_raw, right_raw
    measured_ticks = (abs(left) + abs(right)) / 2
    if measured_ticks < 100:
        display.show(Image.NO)
        print("CALIBRATION_REJECTED left={} right={}".format(left, right))
        return

    config["calibration_samples"] += 1
    config["calibration_ticks_total"] += measured_ticks
    config["ticks_per_meter"] = (
        config["calibration_ticks_total"] / config["calibration_samples"]
    )
    config["calibrated"] = True
    save_config()
    print(
        "CALIBRATION_SAVED sample={} measured={} average={} theoretical={} "
        "left={} right={}".format(
            config["calibration_samples"], measured_ticks,
            config["ticks_per_meter"], THEORETICAL_TICKS_PER_METER, left, right
        )
    )
    enter_idle()


def report_status():
    left, right = update_position()
    average = (left + right) / 2
    distance_m = average / config["ticks_per_meter"]
    heading_rad = (
        (right - left) / config["ticks_per_meter"] / WHEEL_BASE_M
    )
    print(
        "STATUS state={} left={} right={} average={} distance_m={} "
        "heading_rad={} target_ticks={} error={} manual_unknown={}".format(
            state, left, right, average, distance_m, heading_rad,
            target_ticks, target_ticks - average, manual_motion_unknown,
        )
    )


def control_step():
    global state, position_integral, previous_position_error, previous_heading_error
    global last_control_time

    now = running_time()
    elapsed_ms = now - last_control_time
    if elapsed_ms < CONTROL_PERIOD_MS:
        return

    last_control_time = now
    dt = elapsed_ms / 1000
    left, right = update_position()
    average = (left + right) / 2
    position_error = target_ticks - average
    heading_error = left - right

    if manual_motion_unknown:
        emergency_stop()
        print("SAFETY_MANUAL_DIRECTION_UNKNOWN")
        return

    if average > target_ticks + MAX_OVERSHOOT_TICKS:
        emergency_stop()
        print("SAFETY_OVERSHOOT average={} target={}".format(
            average, target_ticks
        ))
        return

    if abs(position_error) <= POSITION_TOLERANCE_TICKS:
        stop_motors()
        state = IDLE
        position_integral = 0.0
        display.show(Image.TARGET)
        print("TARGET_REACHED average={} target={} error={}".format(
            average, target_ticks, position_error
        ))
        return

    if running_time() - run_started > MAX_RUN_TIME_MS:
        emergency_stop()
        print("SAFETY_TIMEOUT")
        return

    position_integral = clamp(
        position_integral + position_error * dt,
        -INTEGRAL_LIMIT,
        INTEGRAL_LIMIT,
    )
    position_derivative = (position_error - previous_position_error) / dt
    heading_derivative = (heading_error - previous_heading_error) / dt

    common_command = (
        config["kp_position"] * position_error
        + config["ki_position"] * position_integral
        + config["kd_position"] * position_derivative
    )
    speed_limit = (
        APPROACH_SPEED
        if abs(position_error) < APPROACH_ZONE_TICKS
        else MAX_SPEED
    )
    common_command = clamp(common_command, -speed_limit, speed_limit)

    if abs(common_command) < MIN_MOVING_SPEED:
        common_command = sign(common_command) * MIN_MOVING_SPEED

    heading_correction = (
        config["kp_heading"] * heading_error
        + config["kd_heading"] * heading_derivative
    )

    correction_sign = sign(common_command)
    left_command = common_command - correction_sign * heading_correction
    right_command = common_command + correction_sign * heading_correction
    set_signed_motors(left_command, right_command)

    display.show(Image.ARROW_N if common_command > 0 else Image.ARROW_S)
    previous_position_error = position_error
    previous_heading_error = heading_error


def handle_a():
    global state
    if state == IDLE:
        if config["calibrated"]:
            start_run()
        else:
            display.show(Image.NO)
            print("CALIBRATION_REQUIRED use A+B")
    elif state == DISTANCE_SELECT:
        config["distance_cm"] += 10
        if config["distance_cm"] > 500:
            config["distance_cm"] = 10
        show_distance()


def handle_b():
    global state
    if state == IDLE:
        state = DISTANCE_SELECT
        show_distance()
    elif state == DISTANCE_SELECT:
        save_config()
        enter_idle()
    elif state == MANUAL_CALIBRATION:
        finish_manual_calibration()
    elif state == RUNNING_TO_TARGET:
        enter_idle()


def handle_combo():
    global state
    if state == RUNNING_TO_TARGET:
        emergency_stop()
    else:
        stop_motors()
        reset_encoders()
        state = MANUAL_CALIBRATION
        display.show("C")
        print("CALIBRATION_STARTED move exactly 1m then press B")


load_config()

try:
    while True:
        if not connected:
            if MAQUEEN_ADDRESS not in i2c.scan():
                display.show(Image.NO)
                sleep(500)
                continue
            write_register(0x0A, (0,))
            connected = True
            enter_idle()
            print(
                "READY ticks_per_meter={} theoretical={} distance_cm={}".format(
                    config["ticks_per_meter"], THEORETICAL_TICKS_PER_METER,
                    config["distance_cm"],
                )
            )

        try:
            both_pressed = button_a.is_pressed() and button_b.is_pressed()
            if both_pressed:
                button_a.was_pressed()
                button_b.was_pressed()
                if not combo_latched:
                    combo_latched = True
                    handle_combo()
            elif combo_latched:
                button_a.was_pressed()
                button_b.was_pressed()
                if not button_a.is_pressed() and not button_b.is_pressed():
                    combo_latched = False
            else:
                if button_a.was_pressed():
                    handle_a()
                if button_b.was_pressed():
                    handle_b()

            if state == RUNNING_TO_TARGET:
                control_step()

            if running_time() - last_report_time >= 1000:
                last_report_time = running_time()
                report_status()

            sleep(10)
        except OSError as error:
            state = IDLE
            connected = False
            display.show(Image.NO)
            print("ERROR Maqueen connection:", error)
finally:
    try:
        stop_motors()
    except OSError:
        pass
