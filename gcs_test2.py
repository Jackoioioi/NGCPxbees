from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]  # .../gcs-infrastructure-main
sys.path.insert(0, str(ROOT))

import threading
import time  # <-- minimal add

import os, sys
print("exe:", sys.executable)
print("cwd:", os.getcwd())
print("sys.path[0]:", sys.path[0])
print("sys.path (first 5):", sys.path[:5])

from Communication.XBee.XBee import XBee

# use [System.IO.Ports.SerialPort]::GetPortNames() in temrinal to get your computer's port

PORT = "COM7"
BAUD_RATE = 9600

transmit = False
transmit_lock = threading.Lock()
transmit_data = ""

stop_event = threading.Event()  # <-- minimal add


def manage_serial(xbee: XBee):
    global transmit
    try:
        while (not stop_event.is_set()) and xbee is not None and xbee.ser is not None:
            data = xbee.retrieve_data()

            if transmit:
                print("Sending: %s" % transmit_data)
                xbee.transmit_data(transmit_data)
                print("Data sent")
                transmit = False

            if data:
                print("Retrieved data:", data)

            time.sleep(0.01)  # <-- minimal add: prevents 100% CPU busy loop

    except Exception as e:
        print(f"Error: {e}")


def listen_keyboard():
    global transmit_data, transmit
    try:
        while not stop_event.is_set():
            try:
                line = input()
            except EOFError:
                # Terminal closed / input stream ended
                stop_event.set()
                break

            if line.strip().lower() in ("exit", "quit"):
                stop_event.set()
                break

            transmit_data = line
            transmit = True

    except KeyboardInterrupt:
        stop_event.set()


def main():
    xbee = XBee(PORT, BAUD_RATE)

    try:
        xbee.open()

        t2 = threading.Thread(target=listen_keyboard, daemon=True)  # <-- daemon
        t1 = threading.Thread(target=manage_serial, args=(xbee,), daemon=True)

        t2.start()
        t1.start()

        # Keep main thread alive so Ctrl+C works reliably
        while not stop_event.is_set():
            time.sleep(0.1)

    except KeyboardInterrupt:
        stop_event.set()

    finally:
        # Always try to close the serial port so XCTU can reconnect later
        try:
            if xbee is not None:
                xbee.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()