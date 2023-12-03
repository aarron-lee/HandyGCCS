#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>
import asyncio
import sys
import time
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff
from .. import constants as cons
from enum import Enum
from evdev import ecodes

handycon = None
gyro_on = False
hid_qam = False

# STEAM res[18] == 128
# QAM res[18] == 64
# Y1 res[20] = 128
# Y2 res[20] = 64
# Y3 res[20] = 32
# M2 res[20] = 8
# M3 res[20] = 4
class HidButtons(Enum):
    LEGION_L = [18, 128]
    LEGION_R = [18, 64]
    Y1 = [20, 128]
    Y2 = [20, 64]
    Y3 = [20, 32]
    M2 = [20, 8]
    M3 = [20, 4]

def is_button(hid_event, button):
    [idx, value] = button.value
    return hid_event[idx] == value

class Gyro(Enum):
    LEFT_GYRO = 0x01
    RIGHT_GYRO = 0x02

class GyroRemapActions(Enum):
    DISABLED = 0x00
    LEFT_JOYSTICK = 0x01
    RIGHT_JOYSTICK = 0x02

# Emit a single event. Skips some logic checks for optimization.
def emit_event(event):
    global handycon
    # handycon.logger.debug(f"Emitting event: {event}")
    # file1 = open("/home/deck/Development/HandyGCCS/logs.txt", "a")
    # file1.write(f"{event}\n")
    # file1.close()
    handycon.ui_device.write_event(event)
    handycon.ui_device.syn()

async def emit_events(events: list):
    global handycon

    for event in events:
        emit_event(event)
        # Pause between multiple events, but not after the last one in the list.
        if event != events[len(events)-1]:
            await asyncio.sleep(handycon.BUTTON_DELAY)

async def handle_button(hid_data, hid_button, new_button):
    global handycon

    if(is_button(hid_data, hid_button) and new_button not in handycon.hid_event_queue):
        # hid_button_pressed
        handycon.hid_event_queue.append(new_button)
        inputs_list = []

        for button in new_button:
            inputs_list.append(create_button_input_event(button, 1))

        await emit_events(inputs_list)
    if(is_button(hid_data, hid_button) and new_button in handycon.hid_event_queue):
        # hid_button_released
        handycon.hid_event_queue.remove(new_button)
        inputs_list = []
        for button in new_button:
            inputs_list.append(create_button_input_event(button, 0))
        await emit_events(inputs_list)

def init_handheld(handheld_controller):
    global handycon
    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.2
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:c2:00.3-3/input0'
    handycon.GAMEPAD_NAME = 'Generic X-Box pad'
    handycon.KEYBOARD_ADDRESS = 'usb-0000:c2:00.3-3/input3'
    handycon.KEYBOARD_NAME = '  Legion Controller for Windows  Keyboard'
    handycon.KEYBOARD_2_NAME = '  Legion Controller for Windows  Mouse'
    handycon.KEYBOARD_2_ADDRESS = 'usb-0000:c2:00.3-3/input3'

def create_button_input_event(button_codes, value):
    t = time.time()
    sec = int(t)
    usec = t % 1
    [type, code] = button_codes 
    return InputEvent(sec, usec, type, code,  value)

# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys, hid_data=None):
    global handycon
    global gyro_on
    global hid_qam

    # Button map shortcuts for easy reference.
    button2 = handycon.button_map["button2"]  # Default QAM
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE

    # HID events
    if (not seed_event or not active_keys) and hid_data:
        await handle_button(hid_data, HidButtons.LEGION_L, button5)
        await handle_button(hid_data, HidButtons.LEGION_R, button2)

    # not HID events
    else:
        ## Loop variables
        button_on = seed_event.value

        # Legion + a = QAM
        if active_keys == [29, 56, 111] and button_on == 1 and button2 not in handycon.event_queue:
            await handycon.handle_key_down(seed_event, button2)
        elif active_keys == [] and seed_event.code in [29, 56, 111] and button_on == 0 and button2 in handycon.event_queue:
            await handycon.handle_key_up(seed_event, button2)

        # Legion + x = keyboard
        if active_keys == [99] and button_on == 1 and button4 not in handycon.event_queue:
            await handycon.handle_key_down(seed_event, button4)
        elif active_keys == [] and seed_event.code in [99] and button_on == 0 and button4 in handycon.event_queue:
            await handycon.handle_key_up(seed_event, button4)

        # Legion + B = MODE
        if active_keys == [24, 29, 125] and button_on == 1 and button5 not in handycon.event_queue:
            await handycon.handle_key_down(seed_event, button5)
        elif active_keys == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button5 in handycon.event_queue:
            await handycon.handle_key_up(seed_event, button5)

        if handycon.last_button:
            await handycon.handle_key_up(seed_event, handycon.last_button)