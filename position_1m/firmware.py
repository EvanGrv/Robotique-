from microbit import *


MAQUEEN_ADDRESS = 0x10
CONFIG_FILE = "position_config.txt"

WHEEL_RADIUS_M = 0.0215
ENCODER_COUNTS_PER_REVOLUTION = 80
THEORETICAL_TICKS_PER_METER = (
    ENCODER_COUNTS_PER_REVOLUTION / (2 * 3.14159265 * WHEEL_RADIUS_M)
)

LOOP_DELAY_MS = 10
POSITION_TOLERANCE_M = 0.005
STABLE_TIME_MS = 500
APPROACH_ZONE_M = 0.15
MAX_SPEED = 80
APPROACH_SPEED = 38
MIN_SPEED = 20
MAX_RUN_TIME_MS = 30000
MAX_RAW_DELTA_TICKS = 100
INTEGRAL_LIMIT_M_S = 0.25
DERIVATIVE_FILTER_ALPHA = 0.20

IDLE = 0
DISTANCE_SELECT = 1
CALIBRATION = 2
MOVING = 3

config = {
    "ticks_per_meter": THEORETICAL_TICKS_PER_METER,
    "calibrated": False,
    "calibration_samples": 0,
    "calibration_ticks_total": 0.0,
    "distance_cm": 100,
    "kp_position": 200.0,
    "ki_position": 5.0,
    "kd_position": 20.0,
    "kp_heading": 400.0,
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
)

state = IDLE
connected = False
combo_latched = False
run_started = 0
stable_started = 0
last_pid_time = running_time()
last_report_time = running_time()
position_integral_m_s = 0.0
filtered_velocity_m_s = 0.0
previous_position_m = 0.0
last_p_term = 0.0
last_i_term = 0.0
last_d_term = 0.0
last_common_command = 0.0

left_raw_previous = 0
right_raw_previous = 0
left_position_m = 0.0
right_position_m = 0.0
manual_direction_unknown = False


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


def reset_encoder_counters():
    write_register(0x04, (0, 0, 0))


def read_raw_encoder_counters():
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


def raw_counter_delta(current, previous):
    delta = (current - previous) & 0xFFFF
    if delta > MAX_RAW_DELTA_TICKS:
        print("IGNORED_DELTA", delta)
        return 0
    return delta


def reset_position():
    global left_raw_previous, right_raw_previous
    global left_position_m, right_position_m, manual_direction_unknown

    reset_encoder_counters()
    left_raw_previous, right_raw_previous = read_raw_encoder_counters()
    left_position_m = 0.0
    right_position_m = 0.0
    manual_direction_unknown = False


def update_position():
    global left_raw_previous, right_raw_previous
    global left_position_m, right_position_m, manual_direction_unknown

    left_raw, right_raw = read_raw_encoder_counters()
    left_direction, right_direction = read_motor_directions()

    left_delta = raw_counter_delta(left_raw, left_raw_previous)
    right_delta = raw_counter_delta(right_raw, right_raw_previous)
    left_sign = direction_sign(left_direction)
    right_sign = direction_sign(right_direction)

    if (left_delta and not left_sign) or (right_delta and not right_sign):
        manual_direction_unknown = True

    left_position_m += left_delta * left_sign / config["ticks_per_meter"]
    right_position_m += right_delta * right_sign / config["ticks_per_meter"]
    left_raw_previous = left_raw
    right_raw_previous = right_raw

    return left_position_m, right_position_m


def motor_values(command):
    speed = int(clamp(abs(command), 0, 240))
    if speed == 0:
        return 0, 0
    if command > 0:
        return 1, speed
    return 2, speed


def set_motors(left_command, right_command):
    left_direction, left_speed = motor_values(left_command)
    right_direction, right_speed = motor_values(right_command)
    write_register(
        0x00,
        (left_direction, left_speed, right_direction, right_speed),
    )


def stop_motors():
    write_register(0x00, (0, 0, 0, 0))


def show_distance():
    display.scroll(str(config["distance_cm"]) + "cm", wait=True, loop=False)
    display.show(Image.SQUARE_SMALL)


def enter_idle():
    global state, stable_started
    stop_motors()
    state = IDLE
    stable_started = 0
    display.show(Image.SQUARE_SMALL)
    print("IDLE A=move B=distance AB=calibrate")


def start_move():
    global state, run_started, stable_started, last_pid_time
    global position_integral_m_s, filtered_velocity_m_s, previous_position_m
    global last_p_term, last_i_term, last_d_term, last_common_command
    reset_position()
    run_started = running_time()
    stable_started = 0
    last_pid_time = run_started
    position_integral_m_s = 0.0
    filtered_velocity_m_s = 0.0
    previous_position_m = 0.0
    last_p_term = 0.0
    last_i_term = 0.0
    last_d_term = 0.0
    last_common_command = 0.0
    state = MOVING
    display.show(Image.ARROW_N)
    print("MOVE target_m={}".format(config["distance_cm"] / 100))


def emergency_stop(reason):
    global state
    stop_motors()
    state = IDLE
    display.show(Image.NO)
    print("EMERGENCY_STOP", reason)


def update_motors():
    global state, stable_started, last_pid_time
    global position_integral_m_s, filtered_velocity_m_s, previous_position_m
    global last_p_term, last_i_term, last_d_term, last_common_command

    left_m, right_m = update_position()
    position_m = (left_m + right_m) / 2
    target_m = config["distance_cm"] / 100
    distance_error_m = target_m - position_m
    heading_error_m = left_m - right_m

    if manual_direction_unknown:
        emergency_stop("manual_direction_unknown")
        return

    now = running_time()
    dt = (now - last_pid_time) / 1000
    if dt <= 0:
        return
    last_pid_time = now

    measured_velocity_m_s = (position_m - previous_position_m) / dt
    previous_position_m = position_m
    filtered_velocity_m_s += DERIVATIVE_FILTER_ALPHA * (
        measured_velocity_m_s - filtered_velocity_m_s
    )

    if abs(distance_error_m) <= POSITION_TOLERANCE_M:
        stop_motors()
        if stable_started == 0:
            stable_started = now
        elif now - stable_started >= STABLE_TIME_MS:
            state = IDLE
            display.show(Image.TARGET)
            print("TARGET position_m={} error_m={}".format(
                position_m, distance_error_m
            ))
        return
    stable_started = 0

    if now - run_started > MAX_RUN_TIME_MS:
        emergency_stop("timeout")
        return

    p_term = config["kp_position"] * distance_error_m
    d_term = -config["kd_position"] * filtered_velocity_m_s
    unsaturated_without_i = p_term + d_term
    speed_limit = (
        APPROACH_SPEED
        if abs(distance_error_m) < APPROACH_ZONE_M
        else MAX_SPEED
    )

    # Conditional integration prevents windup while the output is saturated.
    if (
        abs(unsaturated_without_i) < speed_limit
        or sign(distance_error_m) != sign(unsaturated_without_i)
    ):
        position_integral_m_s = clamp(
            position_integral_m_s + distance_error_m * dt,
            -INTEGRAL_LIMIT_M_S,
            INTEGRAL_LIMIT_M_S,
        )
    i_term = config["ki_position"] * position_integral_m_s
    common_command = p_term + i_term + d_term
    common_command = clamp(common_command, -speed_limit, speed_limit)
    if abs(common_command) < MIN_SPEED:
        common_command = sign(common_command) * MIN_SPEED
    last_p_term = p_term
    last_i_term = i_term
    last_d_term = d_term
    last_common_command = common_command

    heading_correction = config["kp_heading"] * heading_error_m
    movement_sign = sign(common_command)
    left_command = common_command - movement_sign * heading_correction
    right_command = common_command + movement_sign * heading_correction
    set_motors(left_command, right_command)

    display.show(Image.ARROW_N if common_command > 0 else Image.ARROW_S)


def finish_calibration():
    left_raw, right_raw = read_raw_encoder_counters()
    measured_ticks = (left_raw + right_raw) / 2
    if measured_ticks < 100:
        display.show(Image.NO)
        print("CALIBRATION_REJECTED", measured_ticks)
        return

    config["calibration_samples"] += 1
    config["calibration_ticks_total"] += measured_ticks
    config["ticks_per_meter"] = (
        config["calibration_ticks_total"] / config["calibration_samples"]
    )
    config["calibrated"] = True
    save_config()
    print("CALIBRATION sample={} measured={} average={}".format(
        config["calibration_samples"], measured_ticks,
        config["ticks_per_meter"],
    ))
    enter_idle()


def report_status():
    left_m, right_m = update_position()
    position_m = (left_m + right_m) / 2
    print(
        "STATUS state={} left_m={} right_m={} position_m={} target_m={} "
        "error_m={} directions_unknown={} kp={} ki={} kd={} "
        "p={} i={} d={} command={} velocity_m_s={}".format(
            state, left_m, right_m, position_m, config["distance_cm"] / 100,
            config["distance_cm"] / 100 - position_m,
            manual_direction_unknown, config["kp_position"],
            config["ki_position"], config["kd_position"],
            last_p_term, last_i_term, last_d_term, last_common_command,
            filtered_velocity_m_s,
        )
    )


def handle_a():
    global state
    if state == IDLE:
        if config["calibrated"]:
            start_move()
        else:
            display.show(Image.NO)
            print("CALIBRATION_REQUIRED")
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
    elif state == CALIBRATION:
        finish_calibration()
    elif state == MOVING:
        enter_idle()


def handle_combo():
    global state
    if state == MOVING:
        emergency_stop("buttons")
        return

    stop_motors()
    reset_encoder_counters()
    state = CALIBRATION
    display.show("C")
    print("CALIBRATION move exactly 1m then press B")


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
            print("READY ticks_per_meter={} calibrated={}".format(
                config["ticks_per_meter"], config["calibrated"]
            ))

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

            if state == MOVING:
                update_motors()

            if running_time() - last_report_time >= 1000:
                last_report_time = running_time()
                report_status()

            sleep(LOOP_DELAY_MS)
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
