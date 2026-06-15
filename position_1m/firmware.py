from microbit import *


MAQUEEN_ADDRESS = 0x10
CONFIG_FILE = "position_config.txt"
HISTORY_FILE = "calibration_history.txt"

WHEEL_RADIUS_M = 0.0215
WHEEL_BASE_M = 0.085
DEFAULT_TICKS_PER_METER = 539.0

CONTROL_PERIOD_MS = 50
SETTLE_TIME_MS = 800
POSITION_TOLERANCE_TICKS = 2
HOLD_RESTART_TICKS = 5

MAX_SPEED = 85
APPROACH_SPEED = 42
APPROACH_ZONE_TICKS = 90
MIN_SPEED = 24

IDLE = 0
DISTANCE_SELECT = 1
CALIBRATION_MENU = 2
MANUAL_CALIBRATION = 3
PID_TUNE_WAIT = 4
RUNNING = 5
SETTLING = 6
HOLDING = 7

config = {
    "ticks_per_meter": DEFAULT_TICKS_PER_METER,
    "calibrated": True,
    "distance_cm": 100,
    "kp_position": 0.3686,
    "ki_position": 0.0,
    "kd_position": 0.58,
    "kp_heading": 0.75,
    "kd_heading": 0.35,
    "pid_trials": 2,
}
CONFIG_KEYS = (
    "ticks_per_meter",
    "calibrated",
    "distance_cm",
    "kp_position",
    "ki_position",
    "kd_position",
    "kp_heading",
    "kd_heading",
    "pid_trials",
)

state = IDLE
connected = False
combo_latched = False
tuning_trial = False
target_ticks = 0
settle_started = 0
position_integral = 0.0
previous_position_error = 0
previous_heading_error = 0
last_control_time = running_time()
last_report_time = running_time()


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def signed_16(msb, lsb):
    value = (msb << 8) | lsb
    return value - 65536 if value >= 32768 else value


def load_config():
    try:
        with open(CONFIG_FILE, "r") as config_file:
            for line in config_file.read().split("\n"):
                if not line:
                    continue
                key, value = line.strip().split("=", 1)
                if key not in config:
                    continue
                if isinstance(config[key], bool):
                    config[key] = value == "True"
                elif isinstance(config[key], int):
                    config[key] = int(value)
                else:
                    config[key] = float(value)
        print("CONFIG_LOADED", config)
    except (OSError, ValueError):
        print("CONFIG_DEFAULT", config)


def save_config():
    try:
        with open(CONFIG_FILE, "w") as config_file:
            for key in CONFIG_KEYS:
                config_file.write("{}={}\n".format(key, config[key]))
        print("CONFIG_SAVED", config)
    except OSError as error:
        print("ERROR saving config:", error)


def append_history(event):
    try:
        with open(HISTORY_FILE, "a") as history_file:
            history_file.write(event + "\n")
    except OSError as error:
        print("ERROR saving history:", error)


def write_register(register, values=()):
    i2c.write(MAQUEEN_ADDRESS, bytes([register] + list(values)))


def read_encoders():
    write_register(0x04)
    data = i2c.read(MAQUEEN_ADDRESS, 4)
    return signed_16(data[0], data[1]), signed_16(data[2], data[3])


def reset_encoders():
    write_register(0x04, (0, 0, 0))


def set_motors(left_speed, right_speed):
    left_speed = int(clamp(left_speed, 0, 240))
    right_speed = int(clamp(right_speed, 0, 240))
    write_register(
        0x00,
        (1 if left_speed else 0, left_speed,
         1 if right_speed else 0, right_speed),
    )


def stop_motors():
    write_register(0x00, (0, 0, 0, 0))


def reset_pid():
    global position_integral, previous_position_error, previous_heading_error
    global last_control_time
    position_integral = 0.0
    previous_position_error = 0
    previous_heading_error = 0
    last_control_time = running_time()


def show_distance():
    display.scroll(str(config["distance_cm"]) + "cm", wait=True, loop=False)
    display.show(Image.SQUARE_SMALL)


def enter_idle():
    global state, tuning_trial
    stop_motors()
    state = IDLE
    tuning_trial = False
    display.show(Image.SQUARE_SMALL)
    print("IDLE A=run B=distance AB=calibration")


def start_run(is_tuning=False):
    global state, target_ticks, tuning_trial
    stop_motors()
    reset_encoders()
    reset_pid()
    target_ticks = int(
        config["ticks_per_meter"] * config["distance_cm"] / 100
    )
    tuning_trial = is_tuning
    state = RUNNING
    display.show(Image.ARROW_N)
    print("START distance_cm={} target_ticks={} tuning={}".format(
        config["distance_cm"], target_ticks, tuning_trial
    ))


def emergency_stop():
    global state, tuning_trial
    stop_motors()
    state = IDLE
    tuning_trial = False
    display.show(Image.NO)
    print("EMERGENCY_STOP")


def report_status():
    left, right = read_encoders()
    average = (left + right) / 2
    distance = average / config["ticks_per_meter"]
    print(
        "STATUS state={} left={} right={} average={} distance_m={} "
        "target_ticks={} kp={} ki={} kd={} kh={} dh={}".format(
            state, left, right, average, distance, target_ticks,
            config["kp_position"], config["ki_position"],
            config["kd_position"], config["kp_heading"],
            config["kd_heading"],
        )
    )


def control_step():
    global state, settle_started, position_integral
    global previous_position_error, previous_heading_error, last_control_time

    now = running_time()
    elapsed_ms = now - last_control_time
    if elapsed_ms < CONTROL_PERIOD_MS:
        return

    last_control_time = now
    dt = elapsed_ms / 1000
    left, right = read_encoders()
    average = (left + right) / 2
    position_error = target_ticks - average
    heading_error = left - right

    if position_error <= POSITION_TOLERANCE_TICKS:
        stop_motors()
        state = SETTLING
        settle_started = running_time()
        display.show(Image.DIAMOND)
        return

    position_integral = clamp(
        position_integral + position_error * dt, -3000, 3000
    )
    position_derivative = (position_error - previous_position_error) / dt
    heading_derivative = (heading_error - previous_heading_error) / dt

    common_speed = (
        config["kp_position"] * position_error
        + config["ki_position"] * position_integral
        + config["kd_position"] * position_derivative
    )
    speed_limit = (
        APPROACH_SPEED
        if position_error < APPROACH_ZONE_TICKS
        else MAX_SPEED
    )
    common_speed = clamp(common_speed, MIN_SPEED, speed_limit)

    correction = (
        config["kp_heading"] * heading_error
        + config["kd_heading"] * heading_derivative
    )
    set_motors(common_speed - correction, common_speed + correction)

    previous_position_error = position_error
    previous_heading_error = heading_error


def finish_manual_calibration():
    global state
    left, right = read_encoders()
    measured_ticks = (abs(left) + abs(right)) / 2
    if measured_ticks < 100:
        display.show(Image.NO)
        print("CALIBRATION_REJECTED ticks={}".format(measured_ticks))
        return

    config["ticks_per_meter"] = measured_ticks
    config["calibrated"] = True
    config["distance_cm"] = 100
    save_config()
    append_history(
        "MANUAL ticks_per_meter={} left={} right={}".format(
            measured_ticks, left, right
        )
    )
    state = PID_TUNE_WAIT
    display.show("P")
    print("CALIBRATION_SAVED ticks_per_meter={}".format(measured_ticks))
    print("PID_TUNE_READY place at start, A=trial B=finish")


def tune_pid():
    global state
    left, right = read_encoders()
    average = (left + right) / 2
    overshoot = average - target_ticks
    heading_error = left - right

    if overshoot > POSITION_TOLERANCE_TICKS:
        config["kd_position"] = min(
            3.0, config["kd_position"] + min(0.20, overshoot * 0.01)
        )
        config["kp_position"] = max(0.08, config["kp_position"] * 0.97)
    elif overshoot < -POSITION_TOLERANCE_TICKS:
        config["kp_position"] = min(1.5, config["kp_position"] + 0.02)

    if abs(heading_error) > 3:
        config["kp_heading"] = min(2.5, config["kp_heading"] + 0.03)
        config["kd_heading"] = min(2.0, config["kd_heading"] + 0.02)

    config["pid_trials"] += 1
    save_config()
    append_history(
        "PID trial={} target={} final={} overshoot={} heading_error={} "
        "kp={} ki={} kd={} kh={} dh={}".format(
            config["pid_trials"], target_ticks, average, overshoot,
            heading_error, config["kp_position"], config["ki_position"],
            config["kd_position"], config["kp_heading"],
            config["kd_heading"],
        )
    )
    state = PID_TUNE_WAIT
    display.show("P")
    print(
        "PID_TRIAL_RESULT trial={} overshoot={} heading_error={} "
        "kp={} ki={} kd={} kh={} dh={}".format(
            config["pid_trials"], overshoot, heading_error,
            config["kp_position"], config["ki_position"],
            config["kd_position"], config["kp_heading"],
            config["kd_heading"],
        )
    )
    print("PID_TUNE_READY place at start, A=trial B=finish")


def finish_settling():
    global state
    if tuning_trial:
        tune_pid()
    else:
        state = HOLDING
        display.show(Image.TARGET)
        report_status()
        print("TARGET_REACHED")


def handle_a():
    global state
    if state == IDLE:
        if config["calibrated"]:
            start_run(False)
        else:
            state = CALIBRATION_MENU
            display.show("C")
            print("CALIBRATION_REQUIRED A=ticks_per_meter")
    elif state == DISTANCE_SELECT:
        config["distance_cm"] += 10
        if config["distance_cm"] > 500:
            config["distance_cm"] = 10
        show_distance()
    elif state == CALIBRATION_MENU:
        stop_motors()
        reset_encoders()
        state = MANUAL_CALIBRATION
        display.show("C")
        print("MANUAL_CALIBRATION_STARTED move exactly 1m, B=save")
    elif state == PID_TUNE_WAIT:
        start_run(True)


def handle_b():
    global state
    if state == IDLE:
        state = DISTANCE_SELECT
        show_distance()
    elif state == DISTANCE_SELECT:
        save_config()
        enter_idle()
    elif state == CALIBRATION_MENU:
        if not config["calibrated"]:
            display.show(Image.NO)
            print("PID_TUNE_BLOCKED calibrate ticks_per_meter first")
            return
        state = PID_TUNE_WAIT
        display.show("P")
        print("PID_TUNE_READY place at start, A=trial B=finish")
    elif state == MANUAL_CALIBRATION:
        finish_manual_calibration()
    elif state == PID_TUNE_WAIT:
        enter_idle()
    elif state in (RUNNING, SETTLING, HOLDING):
        enter_idle()


def handle_combo():
    global state
    if state in (RUNNING, SETTLING, HOLDING):
        emergency_stop()
    else:
        stop_motors()
        state = CALIBRATION_MENU
        display.show("C")
        print("CALIBRATION_MENU A=ticks_per_meter B=PID")


load_config()

try:
    while True:
        if not connected:
            if MAQUEEN_ADDRESS not in i2c.scan():
                display.show(Image.NO)
                sleep(500)
                continue
            write_register(0x0A, (0,))
            stop_motors()
            connected = True
            enter_idle()
            print("READY ticks_per_meter={} distance_cm={} pid_trials={}".format(
                config["ticks_per_meter"], config["distance_cm"],
                config["pid_trials"],
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

            if state == RUNNING:
                control_step()
            elif state == SETTLING:
                if running_time() - settle_started >= SETTLE_TIME_MS:
                    finish_settling()
            elif state == HOLDING:
                left, right = read_encoders()
                if target_ticks - ((left + right) / 2) > HOLD_RESTART_TICKS:
                    reset_pid()
                    state = RUNNING
                    display.show(Image.ARROW_N)
                    print("RETURN_TO_TARGET")

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
