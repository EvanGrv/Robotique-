#!/usr/bin/env python3
import argparse
import glob
import select
import signal
import sys
import termios
import time
import tty

import serial


KEY_COMMANDS = {
    "z": "forward",
    "w": "forward",
    "s": "back",
    "q": "left",
    "a": "left",
    "d": "right",
    " ": "stop",
    "x": "stop",
}


def find_port():
    ports = sorted(glob.glob("/dev/cu.usbmodem*"))
    if not ports:
        raise RuntimeError("micro:bit introuvable")
    return ports[0]


def send(port, command):
    port.write((command + "\n").encode("utf-8"))
    port.flush()


def print_responses(port):
    while port.in_waiting:
        print(port.readline().decode("utf-8", "replace").rstrip())


def interactive(port):
    print("Z/W=avancer  S=reculer  Q/A=gauche  D=droite  ESPACE/X=stop")
    print("+/-=vitesse  I=statut  Ctrl-C=quitter")
    speed = 80
    active_command = "stop"
    last_send = 0
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            readable, _, _ = select.select([sys.stdin, port], [], [], 0.05)
            if port in readable:
                print_responses(port)
            if sys.stdin in readable:
                key = sys.stdin.read(1).lower()
                if key == "\x03":
                    raise KeyboardInterrupt
                if key in KEY_COMMANDS:
                    active_command = KEY_COMMANDS[key]
                    send(port, active_command)
                    last_send = time.monotonic()
                elif key == "i":
                    send(port, "status")
                elif key in ("+", "-"):
                    speed = max(0, min(240, speed + (10 if key == "+" else -10)))
                    send(port, "speed {}".format(speed))

            if active_command != "stop" and time.monotonic() - last_send >= 0.2:
                send(port, active_command)
                last_send = time.monotonic()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", choices=["stop", "status", "forward", "back", "left", "right"])
    args = parser.parse_args()

    port = serial.Serial(find_port(), 115200, timeout=0.2)

    def stop_and_exit(*_):
        send(port, "stop")
        port.close()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop_and_exit)

    try:
        time.sleep(0.5)
        if args.command:
            send(port, args.command)
            time.sleep(1)
            print_responses(port)
        else:
            interactive(port)
    except KeyboardInterrupt:
        pass
    finally:
        if port.is_open:
            send(port, "stop")
            time.sleep(0.1)
            port.close()


if __name__ == "__main__":
    main()
