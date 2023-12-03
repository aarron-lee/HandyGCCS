#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

import sys
import time
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff
from .. import constants as cons
from .. import legion_configurator as lc
from enum import Enum
from evdev import ecodes

handycon = None
gyro_on = False
hid_qam = False

class Gyro(Enum):
    LEFT_GYRO = 0x01
    RIGHT_GYRO = 0x02

class GyroRemapActions(Enum):
    DISABLED = 0x00
    LEFT_JOYSTICK = 0x01
    RIGHT_JOYSTICK = 0x02

def toggle_gyro():
    command = None
    if gyro_on:
        command = lc.create_gyro_remap_command(Gyro['RIGHT_GYRO'].value, GyroRemapActions['LEFT_JOYSTICK'].value)
    else:
        command = lc.create_gyro_remap_command(Gyro['RIGHT_GYRO'].value, GyroRemapActions['DISABLED'].value)
    lc.send_command(command)

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


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys, hid_data=None):
    global handycon
    global gyro_on
    global hid_qam

    # Button map shortcuts for easy reference.
    button2 = handycon.button_map["button2"]  # Default QAM
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE


    # STEAM res[18] == 128
    # QAM res[18] == 64
    # Y1 res[20] = 128
    # Y2 res[20] = 64
    # Y3 res[20] = 32
    # M2 res[20] = 8
    # M3 res[20] = 4
    if (not seed_event or not active_keys) and hid_data:
        # HID event

        t = time.time()
        sec = int(t)
        usec = t % 1
        fake_seed_event = None
        file1 = open("/home/deck/Development/HandyGCCS/logs.txt", "a")

        file1.write(f'loop {handycon.hid_event_queue} hid_data {hid_data[18]} {hid_data[19]} {hid_data[20]}\n')

        if(hid_data[18] == 128 and button5 not in handycon.hid_event_queue):
            # STEAM/Legion_L pressed
            #  InputEvent: 'sec', 'usec', 'type', 'code', value 
            fake_seed_event = InputEvent(sec, usec, 1, 316,  1)
            handycon.hid_event_queue.append(button5)
            file1.write(f'fake_seed_event down = {fake_seed_event}\n')
            handycon.ui_device.write_event(fake_seed_event)
            handycon.ui_device.syn()

            # await handycon.handle_key_down(fake_seed_event, button5)
        if(hid_data[18] != 128 and button5 in handycon.hid_event_queue):
            # turn off STEAM/Legion_L btn
            handycon.hid_event_queue.remove(button5)
            fake_seed_event = InputEvent(sec, usec, 1, 316,  0)
            file1.write(f'fake_seed_event up = {fake_seed_event}\n')
            handycon.ui_device.write_event(fake_seed_event)
            handycon.ui_device.syn()
            # await handycon.handle_key_up(fake_seed_event, button5)
        file1.close()

    else:
        ## Loop variables
        button_on = seed_event.value

        # file1 = open("/home/deck/Development/HandyGCCS/logs.txt", "a")

        # file1.write(f'seed_event = {seed_event} active_keys={active_keys} button_on={button_on}\n')

        # seed_event = event at 1701534165.778452, code 00, type 00, val 00 active_keys=[274] button_on=0
        # seed_event = event at 1701534170.250365, code 00, type 00, val 00 active_keys=[] button_on=0

        if not gyro_on and active_keys == [274] and seed_event.code == 274 and seed_event.type == 1 and  button_on == 1:
            # toggle gyro on
            gyro_on = True
            # file1.write('gyro on\n')
            toggle_gyro()
        elif gyro_on and active_keys == [] and seed_event.code == 274 and seed_event.type == 1 and button_on == 0:
            # toggle gyro off
            gyro_on = False
            # file1.write("gyro_off\n")
            toggle_gyro()
        # file1.close()

        # # scroll down = QAM
        # if button_on == -1 and seed_event.code == 8 and seed_event.type == 2 and button2 not in handycon.event_queue:
        #     await handycon.handle_key_down(seed_event, button2)
        # elif button_on == -120 and seed_event.code == 11 and seed_event.type == 2 and button2 in handycon.event_queue:
        #     await handycon.handle_key_up(seed_event, button2)

        # # scroll up = MODE
        # if button_on == 1 and seed_event.code == 8 and seed_event.type == 2 and button5 not in handycon.event_queue:
        #     await handycon.handle_key_down(seed_event, button5)
        # elif button_on == 120 and seed_event.code == 11 and seed_event.type == 2 and button5 in handycon.event_queue:
        #     await handycon.handle_key_up(seed_event, button5)

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