#!/usr/bin/env python3
import os

DISKS_3 = ["/dev/sde4", "/dev/sdb5", "/dev/sdd5"]
DISK_4TH = "/dev/sda4"
ALL_DISKS = DISKS_3 + [DISK_4TH]

BLOCK_SIZE = 4096
STEP = 1024 * 1024  # 1 MB steps
MAX_SCAN = 512 * 1024 * 1024  # Scan first 512 MB

def xor_bytes(buffers):
    res = bytearray(buffers[0])
    for b in buffers[1:]:
        for i in range(len(res)):
            res[i] ^= b[i]
    return bytes(res)

def check_mb(fds, offset):
    valid = 0
    non_zero = 0
    # Check 64 blocks (256 KB) at this MB mark
    for i in range(64):
        pos = offset + (i * BLOCK_SIZE)
        chunks = []
        for fd in fds:
            os.lseek(fd, pos, os.SEEK_SET)
            data = os.read(fd, BLOCK_SIZE)
            chunks.append(data)
        if all(c == b'\x00' * BLOCK_SIZE for c in chunks):
            continue
        non_zero += 1
        if xor_bytes(chunks) == b'\x00' * BLOCK_SIZE:
            valid += 1
    if non_zero == 0:
        return "ALL_ZERO"
    return f"{(valid / non_zero)*100:5.1f}%"

def main():
    fds_all = [os.open(d, os.O_RDONLY) for d in ALL_DISKS]
    fds_3 = fds_all[:3]

    print(f"{'Offset (MB)':<12} | {'Byte Offset':<15} | {'3-Disk XOR':<10} | {'4-Disk XOR':<10}")
    print("-" * 56)

    for offset in range(0, MAX_SCAN, STEP):
        r3 = check_mb(fds_3, offset)
        r4 = check_mb(fds_all, offset)
        # Only print interesting transitions or every 16 MB
        if r3 not in ("ALL_ZERO", "  0.0%") or r4 not in ("ALL_ZERO", "  0.0%") or (offset % (16 * STEP) == 0):
            print(f"{offset // STEP:<12} | {offset:<15} | {r3:<10} | {r4:<10}")

if __name__ == "__main__":
    main()
