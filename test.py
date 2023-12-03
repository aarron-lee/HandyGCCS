import hid
import time
import asyncio
vendor_id = 0x17ef  # 6127
product_id = 0x6182 # 24962

# 13 5 =  trackpad
# 13 34
# 13 14

# 65440 1

# 1 6 mouse wheel
# 1 2 
# 1 1

# usage_page = 65440
# usage = 1

usage_page = 13
usage = 5

d = None

devices = hid.enumerate(vendor_id, product_id)
for idx, device in enumerate(devices):
    if device['usage_page'] == usage_page and device['usage'] == usage:
        d = hid.Device(path=device['path'])
    print(f"Device {idx + 1}:")
    print(f"  Path: {device['path']}")
    print(f"  Vendor ID: {device['vendor_id']}")
    print(f"  Product ID: {device['product_id']}")
    print(f"  Serial Number: {device['serial_number']}")
    print(f"  Release Number: {device['release_number']}")
    print(f"  Manufacturer String: {device['manufacturer_string']}")
    print(f"  Product String: {device['product_string']}")
    print(f"  Usage Page: {device['usage_page']}")
    print(f"  Usage: {device['usage']}")
    print("-------------------------------")

# d.nonblocking = 1

count = 1

# STEAM res[18] == 128
# QAM res[18] == 64
# Y1 res[20] = 128
# Y2 res[20] = 64
# Y3 res[20] = 32
# M2 res[20] = 8
# M3 res[20] = 4


while(True):
    res = d.read(64)
    # print(res)
    if(res[20] == 4):
        print(f"found!! {count}")
        count+=1
        # print(res[19])
        # print(res[18])
        # print(res[20])

    time.sleep(0.01)
