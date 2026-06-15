from microbit import *


MAQUEEN_ADDRESS = 0x10


def write_register(register, values=()):
    i2c.write(MAQUEEN_ADDRESS, bytes([register] + list(values)))


def read_register(register, length):
    write_register(register)
    return i2c.read(MAQUEEN_ADDRESS, length)


def stop_motors():
    # Left direction/speed, then right direction/speed.
    write_register(0x00, (0, 0, 0, 0))


def main():
    display.show(Image.SQUARE)
    addresses = i2c.scan()
    print("I2C_ADDRESSES:", [hex(address) for address in addresses])

    if MAQUEEN_ADDRESS not in addresses:
        print("MAQUEEN_NOT_FOUND: expected address 0x10")
        display.show(Image.NO)
        return

    stop_motors()

    version_length = read_register(0x32, 1)[0]
    version = read_register(0x33, version_length)
    motor_state = read_register(0x00, 4)
    line_digital = read_register(0x1D, 1)[0]
    line_analog = read_register(0x1E, 12)

    print("MAQUEEN_FOUND: 0x10")
    print("VERSION:", version)
    print("MOTORS [left_dir, left_speed, right_dir, right_speed]:",
          list(motor_state))
    print("LINE_DIGITAL:", bin(line_digital))
    print("LINE_ANALOG_RAW:", list(line_analog))
    print("MICROBIT_TEMPERATURE_C:", temperature())
    print("MICROBIT_ACCELEROMETER:", accelerometer.get_values())

    display.show(Image.YES)


main()
