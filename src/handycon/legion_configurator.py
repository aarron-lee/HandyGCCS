# MIT License

# Copyright (c) 2019 Austin Morton

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import ctypes
import atexit

__all__ = ['HIDException', 'DeviceInfo', 'Device', 'enumerate']


hidapi = None
library_paths = (
    'libhidapi-hidraw.so',
    'libhidapi-hidraw.so.0',
    'libhidapi-libusb.so',
    'libhidapi-libusb.so.0',
    'libhidapi-iohidmanager.so',
    'libhidapi-iohidmanager.so.0',
    'libhidapi.dylib',
    'hidapi.dll',
    'libhidapi-0.dll'
)

for lib in library_paths:
    try:
        hidapi = ctypes.cdll.LoadLibrary(lib)
        break
    except OSError:
        pass
else:
    error = "Unable to load any of the following libraries:{}"\
        .format(' '.join(library_paths))
    raise ImportError(error)


hidapi.hid_init()
atexit.register(hidapi.hid_exit)


class HIDException(Exception):
    pass


class DeviceInfo(ctypes.Structure):
    def as_dict(self):
        ret = {}
        for name, type in self._fields_:
            if name == 'next':
                continue
            ret[name] = getattr(self, name, None)

        return ret

DeviceInfo._fields_ = [
    ('path', ctypes.c_char_p),
    ('vendor_id', ctypes.c_ushort),
    ('product_id', ctypes.c_ushort),
    ('serial_number', ctypes.c_wchar_p),
    ('release_number', ctypes.c_ushort),
    ('manufacturer_string', ctypes.c_wchar_p),
    ('product_string', ctypes.c_wchar_p),
    ('usage_page', ctypes.c_ushort),
    ('usage', ctypes.c_ushort),
    ('interface_number', ctypes.c_int),
    ('next', ctypes.POINTER(DeviceInfo)),
]

hidapi.hid_init.argtypes = []
hidapi.hid_init.restype = ctypes.c_int
hidapi.hid_exit.argtypes = []
hidapi.hid_exit.restype = ctypes.c_int
hidapi.hid_enumerate.argtypes = [ctypes.c_ushort, ctypes.c_ushort]
hidapi.hid_enumerate.restype = ctypes.POINTER(DeviceInfo)
hidapi.hid_free_enumeration.argtypes = [ctypes.POINTER(DeviceInfo)]
hidapi.hid_free_enumeration.restype = None
hidapi.hid_open.argtypes = [ctypes.c_ushort, ctypes.c_ushort, ctypes.c_wchar_p]
hidapi.hid_open.restype = ctypes.c_void_p
hidapi.hid_open_path.argtypes = [ctypes.c_char_p]
hidapi.hid_open_path.restype = ctypes.c_void_p
hidapi.hid_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
hidapi.hid_write.restype = ctypes.c_int
hidapi.hid_read_timeout.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
hidapi.hid_read_timeout.restype = ctypes.c_int
hidapi.hid_read.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
hidapi.hid_read.restype = ctypes.c_int
hidapi.hid_get_input_report.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
hidapi.hid_get_input_report.restype = ctypes.c_int
hidapi.hid_set_nonblocking.argtypes = [ctypes.c_void_p, ctypes.c_int]
hidapi.hid_set_nonblocking.restype = ctypes.c_int
hidapi.hid_send_feature_report.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
hidapi.hid_send_feature_report.restype = ctypes.c_int
hidapi.hid_get_feature_report.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
hidapi.hid_get_feature_report.restype = ctypes.c_int
hidapi.hid_close.argtypes = [ctypes.c_void_p]
hidapi.hid_close.restype = None
hidapi.hid_get_manufacturer_string.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_size_t]
hidapi.hid_get_manufacturer_string.restype = ctypes.c_int
hidapi.hid_get_product_string.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_size_t]
hidapi.hid_get_product_string.restype = ctypes.c_int
hidapi.hid_get_serial_number_string.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_size_t]
hidapi.hid_get_serial_number_string.restype = ctypes.c_int
hidapi.hid_get_indexed_string.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_size_t]
hidapi.hid_get_indexed_string.restype = ctypes.c_int
hidapi.hid_error.argtypes = [ctypes.c_void_p]
hidapi.hid_error.restype = ctypes.c_wchar_p


def enumerate(vid=0, pid=0):
    ret = []
    info = hidapi.hid_enumerate(vid, pid)
    c = info

    while c:
        ret.append(c.contents.as_dict())
        c = c.contents.next

    hidapi.hid_free_enumeration(info)

    return ret


class Device(object):
    def __init__(self, vid=None, pid=None, serial=None, path=None):
        if path:
            self.__dev = hidapi.hid_open_path(path)
        elif serial:
            serial = ctypes.create_unicode_buffer(serial)
            self.__dev = hidapi.hid_open(vid, pid, serial)
        elif vid and pid:
            self.__dev = hidapi.hid_open(vid, pid, None)
        else:
            raise ValueError('specify vid/pid or path')

        if not self.__dev:
            raise HIDException('unable to open device')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def __hidcall(self, function, *args, **kwargs):
        if not self.__dev:
            raise HIDException('device closed')

        ret = function(*args, **kwargs)

        if ret == -1:
            err = hidapi.hid_error(self.__dev)
            raise HIDException(err)
        return ret

    def __readstring(self, function, max_length=255):
        buf = ctypes.create_unicode_buffer(max_length)
        self.__hidcall(function, self.__dev, buf, max_length)
        return buf.value

    def write(self, data):
        return self.__hidcall(hidapi.hid_write, self.__dev, data, len(data))

    def read(self, size, timeout=None):
        data = ctypes.create_string_buffer(size)

        if timeout is None:
            size = self.__hidcall(hidapi.hid_read, self.__dev, data, size)
        else:
            size = self.__hidcall(
                hidapi.hid_read_timeout, self.__dev, data, size, timeout)

        return data.raw[:size]

    def get_input_report(self, report_id, size):
        data = ctypes.create_string_buffer(size)

        # Pass the id of the report to be read.
        data[0] = bytearray((report_id,))

        size = self.__hidcall(
            hidapi.hid_get_input_report, self.__dev, data, size)
        return data.raw[:size]

    def send_feature_report(self, data):
        return self.__hidcall(hidapi.hid_send_feature_report,
                              self.__dev, data, len(data))

    def get_feature_report(self, report_id, size):
        data = ctypes.create_string_buffer(size)

        # Pass the id of the report to be read.
        data[0] = bytearray((report_id,))

        size = self.__hidcall(
            hidapi.hid_get_feature_report, self.__dev, data, size)
        return data.raw[:size]

    def close(self):
        if self.__dev:
            hidapi.hid_close(self.__dev)
            self.__dev = None

    @property
    def nonblocking(self):
        return getattr(self, '_nonblocking', 0)

    @nonblocking.setter
    def nonblocking(self, value):
        self.__hidcall(hidapi.hid_set_nonblocking, self.__dev, value)
        setattr(self, '_nonblocking', value)

    @property
    def manufacturer(self):
        return self.__readstring(hidapi.hid_get_manufacturer_string)

    @property
    def product(self):
        return self.__readstring(hidapi.hid_get_product_string)

    @property
    def serial(self):
        return self.__readstring(hidapi.hid_get_serial_number_string)

    def get_indexed_string(self, index, max_length=255):
        buf = ctypes.create_unicode_buffer(max_length)
        self.__hidcall(hidapi.hid_get_indexed_string,
                       self.__dev, index, buf, max_length)
        return buf.value


import time
from enum import Enum
# Global variables
vendor_id = 0x17EF
product_id_match = lambda x: x & 0xFFF0 == 0x6180
usage_page = 0xFFA0
global_config = None  # Global configuration for the device

class Gyro(Enum):
    LEFT_GYRO = 0x01
    RIGHT_GYRO = 0x02

class GyroRemapActions(Enum):
    DISABLED = 0x00
    LEFT_JOYSTICK = 0x01
    RIGHT_JOYSTICK = 0x02

# Enumerate and set the global configuration
for dev in enumerate(vendor_id):
    if product_id_match(dev["product_id"]) and dev["usage_page"] == usage_page:
        global_config = dev
        break

if not global_config:
    print("Legion go configuration device not found.")
else:
    print(global_config)


def send_command(command):
    assert len(command) == 64 and global_config
    try:
        with Device(path=global_config['path']) as device:
            device.write(command)
            print("Command sent successfully.")
    except IOError as e:
        print(f"Error opening HID device: {e}")


def create_touchpad_command(enable):
    """
    Create a command to enable or disable the touchpad.

    :param enable: bool - True to enable, False to disable the touchpad
    :return: bytes - The command byte array
    """
    enable_byte = 0x01 if enable else 0x00

    command = [
        0x05,
        0x06,  # Report ID and Length
        0x6B,  # Command (Nibble 6 + b)
        0x02,  # Command sub-parameter
        0x04,  # Right Controller
        enable_byte,  # Enable/Disable flag
        0x01   # All commands end with 0x01
    ]

    byte_command = bytes(command)
    # Pad the byte_command with 0xCD to meet the length of 64 bytes
    buffered_command = byte_command + bytes([0xCD] * (64 - len(byte_command)))
    return buffered_command

def create_rgb_control_command(controller, mode, color, brightness, speed, profile=0x01, on=True):
    """
    Create a command to control the RGB LEDs, including setting the profile and turning them on or off.

    :param controller: byte - The controller byte (0x03 for left, 0x04 for right)
    :param mode: byte - The mode of the LED (e.g., 0x01 for solid, 0x02 for blinking)
    :param color: bytes - The RGB color value (e.g., b'\xFF\x00\x00' for red)
    :param brightness: byte - The brightness value (0x00 to 0x64)
    :param speed: byte - The speed setting for dynamic modes (0x00 to 0x64, higher is slower)
    :param profile: byte - The profile number
    :param on: bool - True to turn on, False to turn off the RGB LEDs
    :return: bytes - The command byte array
    """
    on_off_byte = 0x01 if on else 0x00
    command = [
        0x05, 0x0c if on else 0x06,  # Report ID and Length (0x0c for setting profile, 0x06 for on/off)
        0x72 if on else 0x70,        # Command (Nibble 7 + 2 for profile, 7 + 0 for on/off)
        0x01, controller
    ]

    if on:
        # Adding profile settings when turning on
        command += [mode] + list(color) + [brightness, speed, profile, 0x01]
    else:
        # Adding the on/off byte when turning off
        command += [on_off_byte, 0x01]

    return bytes(command) + bytes([0xCD] * (64 - len(command)))

def create_rgb_on_off_command(controller, on):
    """
    Create a command to turn the RGB LEDs on or off.

    :param controller: byte - The controller byte (e.g., 0x03 for left, 0x04 for right)
    :param on: bool - True to turn on, False to turn off
    :return: bytes - The command byte array
    """
    on_off_byte = 0x01 if on else 0x00
    command = [
        0x05, 0x06,  # Report ID and Length
        0x70,        # Command (Nibble 7 + 0)
        0x02,        # Sub-parameter
        controller,  # Controller
        on_off_byte, # On/Off
        0x01         # Command end marker
    ]
    return bytes(command) + bytes([0xCD] * (64 - len(command)))

def create_gyro_remap_command(gyro, joystick):
    """
    Create a command for gyro remapping.

    :param gyro: byte - The gyro setting (e.g., 0x01, 0x02)
    :param joystick: byte - The joystick value (e.g., 0x00, 0x01, 0x02)
    :return: bytes - The command byte array
    """
    command = [
        0x05, 0x08,  # Report ID and Length
        0x6a,        # Command (Nibble 6 + a)
        0x06, 0x01, 0x01,  # Sub-parameters
        gyro, joystick,
        0x01         # Command end marker
    ]
    return bytes(command) + bytes([0xCD] * (64 - len(command)))

def create_button_remap_command(controller, button, action):
    """
    Create a command for button remapping.

    :param controller: byte - The controller byte (0x03 for left, 0x04 for right)
    :param button: byte - The button to remap. Button codes:
                    0x1c: Y1, 0x1d: Y2, 0x1e: Y3, 0x21: M2, 0x22: M3
    :param action: byte - The action to assign to the button. Action codes:
                   0x00: Disabled, 0x03: Left Stick Click, 0x04: Left Stick Up,
                   0x05: Left Stick Down, 0x06: Left Stick Left, 0x07: Left Stick Right,
                   0x08: Right Stick Click, 0x09: Right Stick Up, 0x0a: Right Stick Down,
                   0x0b: Right Stick Left, 0x0c: Right Stick Right, 0x0d: D-Pad Up,
                   0x0e: D-Pad Down, 0x0f: D-Pad Left, 0x10: D-Pad Right,
                   0x12: A, 0x13: B, 0x14: X, 0x15: Y, 0x16: Left Bumper,
                   0x17: Left Trigger, 0x18: Right Bumper, 0x19: Right Trigger,
                   0x23: View, 0x24: Menu
    :return: bytes - The command byte array
    """
    command = [
        0x05, 0x07,  # Report ID and Length
        0x6c,        # Command (Nibble 6 + c)
        0x02, controller, button, action,
        0x01         # Command end marker
    ]
    return bytes(command) + bytes([0xCD] * (64 - len(command)))

def create_vibration_command(controller, vibration_level):
    """
    Create a command to control the vibration of the controller.

    :param controller: byte - The controller byte (0x03 for left, 0x04 for right)
    :param vibration_level: byte - Vibration level (0x00: Off, 0x01: Weak, 0x02: Medium, 0x03: Strong)
    :return: bytes - The command byte array
    """
    command = [
        0x05, 0x06,  # Report ID and Length
        0x67,        # Command (Nibble 6 + 7)
        0x02,        # Sub-parameter
        controller, vibration_level,
        0x01         # Command end marker
    ]
    return bytes(command) + bytes([0xCD] * (64 - len(command)))

def create_fps_remap_command(controller, profile, button, action):
    """
    Create a command for FPS remapping.

    :param controller: byte - The controller byte (0x03 for left, 0x04 for right)
    :param profile: byte - The profile number (from 0x01 to 0x04)
    :param button: byte - The button to remap
    :param action: byte - The action to assign to the button
    :return: bytes - The command byte array
    """
    command = [
        0x05, 0x08,  # Report ID and Length
        0x6c,        # Command (Nibble 6 + c)
        0x04,        # Sub-parameter
        controller, profile, button, action,
        0x01         # Command end marker
    ]
    return bytes(command) + bytes([0xCD] * (64 - len(command)))

# # vibration_command = create_vibration_command(0x04, 0x01)  # Strong vibration on right 
# # send_command(vibration_command)
# # vibration_command = create_vibration_command(0x03, 0x03)  # Strong vibration on right controller
# send_command(vibration_command)
# gyro_left = create_gyro_remap_command(0x02, 0x02)
# send_command(gyro_left)
# gyro_right = create_gyro_remap_command(0x01, 0x00)
# send_command(gyro_right)
