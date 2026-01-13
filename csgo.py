#!/bin/python3
import time
import struct
import os

dwLocalPlayer = 0xDB75DC
dwEntityList = 0x4DD345C
dwClientState = 0x58CFC4

# player
m_hMyWeapons = 0x2E08

# base attributable
m_flFallbackWear = 0x31E0
m_nFallbackPaintKit = 0x31D8
m_nFallbackSeed = 0x31DC
m_nFallbackStatTrak = 0x31E4
m_nForceBone = 0x268C
m_iItemDefinitionIndex = 0x2FBA
m_iItemIDHigh = 0x2FD0
m_iEntityQuality = 0x2FBC
m_iAccountID = 0x2FD8
m_OriginalOwnerXuidLow = 0x31D0

class Memory:
    processname = ""
    pid = ""

    def __init__(self, processname):
        self.processname = processname
        for dir in os.scandir("/proc/"):
            if dir.is_dir() and os.path.exists(f"{dir.path}/cmdline"):
                file_path = f"{dir.path}/cmdline"
                if processname in open(file_path, "r").readline():
                    print(open(file_path, "r").readline())
                    #self.pid = dir.path.replace("/proc/", "")
                #    break

        if self.pid == "":
            exit("csgo: process not found")

    def module_address(self, modulename):
        maps_file = f"/proc/{self.pid}/maps"

        with open(maps_file, "r") as maps:
            for line in maps:
                parts = line.split()
                address_range, perms = parts[0], parts[1]
                if 'r' in perms and "w" in perms:
                    start, end = (int(addr, 16) for addr in address_range.split('-'))
                    return start

    def read(self, address, length):
        try:
            with open(f"/proc/{self.pid}/mem", "rb") as mem:
                mem.seek(address)
                print("test")
                data = mem.read(length)
                print(f"Data from {hex(address)}-{hex(address + length)}: {data}")
            print(data)
            return data
        except Exception as e:
            print(f"Error reading memory at {hex(address)}: {e}")
            return None

    def write(self, address, value):
        with open(f"/proc/{self.pid}/mem", "wb") as mem:
            mem.seek(address)
            mem.write(value)
        mem.close()

def int_to_uint32_le_str(value):
    # Mask to 32 bits (wrap around if needed)
    wrapped = int(value) & 0xFFFFFFFF

    # 4‑byte little‑endian bytes object
    le_bytes = wrapped.to_bytes(4, byteorder="little", signed=False)

    # Convert each byte to two‑digit hex and concatenate
    return "".join(f"{b:02x}" for b in le_bytes)

def int_to_float_le_str(value):
    float_value = float(value)
    binary_representation = ''
    for i in range(32):
        binary_representation = str(int(float_value) & (1 << i)) + binary_representation
    return str(binary_representation)

def GetWeaponPaint(item):
    if item == 1:
        return 711
    elif item == 4:
        return 38
    elif item == 7:
        return 600
    elif item == 16:
        return 400
    elif item == 9:
        return 887
    elif item == 61:
        return 653
    else:
        return 0

if __name__ == "__main__":
    csgo = Memory("csgo_linux64")
    client = csgo.module_address("client_client.so")
    engine = csgo.module_address("client_engine.so")

    #try:
    while True:
        time.sleep(0.5)
        localPlayer = csgo.read(int(client + dwEntityList), 8)
        print(localPlayer)
        weapons = csgo.read(localPlayer + m_hMyWeapons, 4*8)
        tmp = [weapons[:5], weapons[5:9], weapons[9:13], weapons[13:]]
        weapons = tmp

        for i in weapons:
            weapon = csgo.read((client + dwEntityList + (i & 0xFFF) * 0x10) - 0x10, 8)

            if not weapon:
                continue

            paint = GetWeaponPaint(csgo.read(weapon + m_iItemDefinitionIndex, 2))
            if paint:
                shouldupdate = csgo.read(weapon + m_nFallbackPaintKit, 4) != paint

                csgo.write(weapon + m_iItemIDHigh, int_to_uint32_le_str(-1))
                csgo.write(weapon + m_nFallbackPaintKit, int_to_uint32_le_str(paint))
                csgo.write(weapon + m_flFallbackWear, struct.pack("f", 0.1))

                if shouldupdate:
                    csgo.write(csgo.read(engine + dwClientState, 8) + 0x174, int_to_uint32_le_str(-1))
    #except:
     #   print("exit")