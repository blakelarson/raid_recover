#!/usr/bin/env python3
import os

DISKS = ["/dev/sde4", "/dev/sdb5", "/dev/sdd5", "/dev/sda4"]
fds = [os.open(d, os.O_RDONLY) for d in DISKS]

# Check exact offset between 127 MB and 130 MB where 4-disk data begins
for pos in range(127 * 1024 * 1024, 130 * 1024 * 1024, 4096):
    chunks = []
    for fd in fds:
        os.lseek(fd, pos, os.SEEK_SET)
        chunks.append(os.read(fd, 4096))
    if any(c != b'\x00' * 4096 for c in chunks):
        print(f"First non-zero data at byte: {pos} (Sector {pos // 512}, {pos / (1024*1024):.4f} MB)")
        for name, c in zip(DISKS, chunks):
            has_lvm = b"LABELONE" in c or b"LVM2" in c
            print(f"  {name}: non-zero={c != b'\x00'*4096}, has_LVM_header={has_lvm}")
        break
