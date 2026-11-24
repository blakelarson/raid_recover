#!/usr/bin/env python3
import os

DISKS = ["/dev/sde4", "/dev/sdb5", "/dev/sdd5", "/dev/sda4"]
fds = [os.open(d, os.O_RDONLY) for d in DISKS]

found_lvm = False
found_parity = False

for pos in range(127 * 1024 * 1024, 132 * 1024 * 1024, 512):
    chunks = []
    for fd in fds:
        os.lseek(fd, pos, os.SEEK_SET)
        chunks.append(os.read(fd, 512))

    # 1. Look for LVM2 signature ("LABELONE")
    if not found_lvm:
        for name, c in zip(DISKS, chunks):
            if b"LABELONE" in c:
                print(f"[LVM HEADER] Found on {name} at byte {pos} (Sector {pos // 512}, {pos / (1024*1024):.4f} MB)")
                found_lvm = True

    # 2. Look for first non-zero 4-disk parity match
    if not found_parity and any(c != b'\x00' * 512 for c in chunks):
        xor = bytearray(chunks[0])
        for c in chunks[1:]:
            for i in range(512):
                xor[i] ^= c[i]
        if xor == b'\x00' * 512:
            print(f"[4-DISK DATA] First non-zero parity block at byte {pos} (Sector {pos // 512}, {pos / (1024*1024):.4f} MB)")
            found_parity = True

    if found_lvm and found_parity:
        break

if not found_lvm and not found_parity:
    print("Nothing found in 127-132 MB range.")
