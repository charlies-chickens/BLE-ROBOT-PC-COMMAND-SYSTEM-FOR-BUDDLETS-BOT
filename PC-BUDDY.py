import subprocess
import sys

def install_requirements():
    try:
        import pkg_resources
        pkg_resources.require(open("requirements.txt").read().split())
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

install_requirements()

import asyncio
import tkinter as tk
import threading
import time
from bleak import BleakScanner, BleakClient

client = None
char_uuid = None

sending = False

held = set()

# Commands! (Took me a while to figure out!)

COMMANDS = {
    "stop": "5A 6B 02 00 04 00 00 00 00 CB",
    "forward": "5A 6B 02 00 04 00 02 00 03 D0",
    "backward": "5A 6B 02 00 04 00 01 00 F2 BE",
    "left": "5A 6B 02 00 04 01 00 A5 00 71",
    "right": "5A 6B 02 00 04 02 00 FF 00 CC"
}


# ---------------- BLE ----------------

async def scan_ble():
    devices = await BleakScanner.discover()
    device_list.delete(0, tk.END)

    for d in devices:
        name = d.name if d.name else "Unknown"
        device_list.insert(tk.END, f"{name} | {d.address}")


async def connect_ble(address):
    global client, char_uuid

    status.set("Connecting...")

    client = BleakClient(address)
    await client.connect()

    for service in client.services:
        for char in service.characteristics:
            if "write" in char.properties and char_uuid is None:
                char_uuid = char.uuid

    status.set("Connected")


async def send_packet(cmd):

    if client is None or char_uuid is None:
        return

    packet = bytes.fromhex(COMMANDS[cmd])
    await client.write_gatt_char(char_uuid, packet)


# ---------------- MOVEMENT LOGIC ----------------

def get_current_cmd():

    if "left" in held:
        return "left"

    if "right" in held:
        return "right"

    if "forward" in held:
        return "forward"

    if "backward" in held:
        return "backward"

    return "stop"


def movement_loop():

    global sending

    last = None

    while sending:

        cmd = get_current_cmd()

        if cmd != last:
            asyncio.run(send_packet(cmd))
            last = cmd

        time.sleep(0.1)


def update_movement():

    global sending

    if not sending:
        sending = True
        threading.Thread(target=movement_loop, daemon=True).start()


# ---------------- INPUT HANDLERS ----------------

def press(cmd):

    held.add(cmd)
    update_movement()


def release(cmd):

    if cmd in held:
        held.remove(cmd)


# ---------------- THREAD WRAPPER ----------------

def run_async(coro):
    asyncio.run(coro)


def scan():
    threading.Thread(target=run_async, args=(scan_ble(),)).start()


def connect():
    try:
        selection = device_list.get(device_list.curselection())
        address = selection.split("|")[1].strip()
    except:
        status.set("Select device first")
        return

    threading.Thread(target=run_async, args=(connect_ble(address),)).start()


# ---------------- GUI ----------------

root = tk.Tk()
root.title("RobotHax Controller")
root.geometry("360x450")

status = tk.StringVar()
status.set("Not connected")

tk.Button(root, text="Scan Bluetooth", command=scan).pack(pady=5)

device_list = tk.Listbox(root, width=40)
device_list.pack(pady=5)

tk.Button(root, text="Connect Board", command=connect).pack(pady=5)

tk.Label(root, textvariable=status).pack(pady=10)

controls = tk.Frame(root)
controls.pack(pady=20)

forward = tk.Button(controls, text="Forward", width=10)
forward.grid(row=0, column=1)

left = tk.Button(controls, text="Left", width=10)
left.grid(row=1, column=0)

right = tk.Button(controls, text="Right", width=10)
right.grid(row=1, column=2)

back = tk.Button(controls, text="Backward", width=10)
back.grid(row=2, column=1)

# Button bindings
forward.bind("<ButtonPress>", lambda e: press("forward"))
forward.bind("<ButtonRelease>", lambda e: release("forward"))

left.bind("<ButtonPress>", lambda e: press("left"))
left.bind("<ButtonRelease>", lambda e: release("left"))

right.bind("<ButtonPress>", lambda e: press("right"))
right.bind("<ButtonRelease>", lambda e: release("right"))

back.bind("<ButtonPress>", lambda e: press("backward"))
back.bind("<ButtonRelease>", lambda e: release("backward"))


# ---------------- KEYBOARD ----------------

root.bind("<KeyPress-w>", lambda e: press("forward"))
root.bind("<KeyRelease-w>", lambda e: release("forward"))

root.bind("<KeyPress-s>", lambda e: press("backward"))
root.bind("<KeyRelease-s>", lambda e: release("backward"))

root.bind("<KeyPress-a>", lambda e: press("left"))
root.bind("<KeyRelease-a>", lambda e: release("left"))

root.bind("<KeyPress-d>", lambda e: press("right"))
root.bind("<KeyRelease-d>", lambda e: release("right"))

root.mainloop()
