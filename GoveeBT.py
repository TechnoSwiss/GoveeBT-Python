#!/usr/bin/env python3

import asyncio
from bleak import BleakScanner
from datetime import datetime

def decode_govee_data(name, mfg_id, data):
    try:
        # H5074 - ec88, 7 bytes
        if mfg_id == 0xEC88 and len(data) == 7 and name.startswith('Govee_H5074_'):
            i_temp = (data[2] << 8) | data[1]
            i_hum = (data[4] << 8) | data[3]
            temp = i_temp / 100.0
            hum = i_hum / 100.0
            battery = data[5]
            return [temp], hum, battery

        # H5075 - ec88, 6 bytes
        elif mfg_id == 0xEC88 and len(data) == 6 and name.startswith('GVH5075_'):
            i_temp = (data[1] << 16) | (data[2] << 8) | data[3]
            negative = i_temp & 0x800000
            i_temp &= 0x7FFFFF
            temp = (i_temp // 1000) / 10.0
            if negative:
                temp = -temp
            hum = (i_temp % 1000) / 10.0
            battery = data[4]
            return [temp], hum, battery

        # H5177 / H5174 / H5100 - 0001, 6 bytes
        elif mfg_id == 0x0001 and len(data) == 6 and name.startswith(('GVH5177_', 'GVH5174_', 'GVH5100_')):
            i_temp = (data[2] << 16) | (data[3] << 8) | data[4]
            negative = i_temp & 0x800000
            i_temp &= 0x7FFFFF
            temp = i_temp / 10000.0
            if negative:
                temp = -temp
            hum = (i_temp % 1000) / 10.0
            battery = data[5]
            return [temp], hum, battery

        # H5179 - ec88, 9 bytes
        elif mfg_id == 0xEC88 and len(data) == 9 and name.startswith('GVH5179'):
            i_temp = (data[5] << 8) | data[4]
            i_hum = (data[7] << 8) | data[6]
            temp = i_temp / 100.0
            hum = i_hum / 100.0
            battery = data[8]
            return [temp], hum, battery

        # H5183 - 14 bytes, no mfg_id match
        elif len(data) == 14 and name.startswith('GVH5183'):
            i_temp = (data[8] << 8) | data[9]
            i_alarm = (data[10] << 8) | data[11]
            battery = data[5] & 0x7F
            return [i_temp / 100.0, i_alarm / 100.0], 0.0, battery

        # H5182 - 17 bytes, dual probes
        elif len(data) == 17 and name.startswith('GVH5182'):
            temps = [
                ((data[8] << 8) | data[9]) / 100.0,     # probe 1 temp
                ((data[10] << 8) | data[11]) / 100.0,   # probe 1 alarm
                ((data[13] << 8) | data[14]) / 100.0,   # probe 2 temp
                ((data[15] << 8) | data[16]) / 100.0    # probe 2 alarm
            ]
            battery = data[5] & 0x7F
            return temps, 0.0, battery

        # H5055 - 20 bytes
        elif len(data) == 20 and name.startswith('GVH5055'):
            temps = [
                float((data[6] << 8) | data[5]),      # probe 1
                float((data[10] << 8) | data[9]),     # probe 1 high alarm
                float((data[13] << 8) | data[12]),    # probe 2
                float((data[17] << 8) | data[16])     # probe 2 high alarm
            ]
            battery = data[2]
            return temp, 0.0, battery

    except Exception as e:
        print(f"Decode error for {name}: {e}")

    return None

def handle_device(device, advertisement_data):
    name = device.name or ""
    mfg_data = advertisement_data.manufacturer_data

    # Parse manufacturer section (e.g. 0xEC88, 0x0001)
    for mfg_id, data in mfg_data.items():
        result = decode_govee_data(name, mfg_id, bytes(data))
        if result:
            temps, hum, battery = result
            temp_str = ", ".join([f"{t:.2f}" for t in temps])
            print(f"{datetime.now().isoformat()} {device.address} Temp(s): [{temp_str}] C  Humidity: {hum:.1f}%  Battery: {battery}% RSSI: {advertisement_data.rssi} dBm")


async def main():
    scanner = BleakScanner(detection_callback=handle_device)
    await scanner.start()
    try:
        while True:
            await asyncio.sleep(30)
    except KeyboardInterrupt:
        await scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())
