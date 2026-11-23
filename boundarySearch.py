#!/usr/bin/env python3
import os
import sys

# Update these paths if drive letters shift on reboot
DISKS_3 = ["/dev/sde4", "/dev/sdb5", "/dev/sdd5"]
DISK_4TH = "/dev/sda4"
ALL_DISKS = DISKS_3 + [DISK_4TH]

BLOCK_SIZE = 4096
SAMPLE_BLOCKS = 64  # Check 256KB per probe

def xor_bytes(buffers):
    res = bytearray(buffers[0])
    for b in buffers[1:]:
        for i in range(len(res)):
            res[i] ^= b[i]
    return bytes(res)

def test_parity_at_offset(fds, offset):
    """Returns ratio (0.0 to 1.0) of non-zero blocks that pass XOR parity."""
    valid = 0
    non_zero = 0
    for i in range(SAMPLE_BLOCKS):
        pos = offset + (i * BLOCK_SIZE)
        chunks = []
        for fd in fds:
            os.lseek(fd, pos, os.SEEK_SET)
            data = os.read(fd, BLOCK_SIZE)
            if len(data) < BLOCK_SIZE:
                return None
            chunks.append(data)
        
        # Skip empty/all-zero areas (they pass both 3-disk and 4-disk XOR)
        if all(c == b'\x00' * BLOCK_SIZE for c in chunks):
            continue
            
        non_zero += 1
        if xor_bytes(chunks) == b'\x00' * BLOCK_SIZE:
            valid += 1
            
    if non_zero == 0:
        return -1.0  # Region is all zeros
    return valid / non_zero

def main():
    fds_all = [os.open(d, os.O_RDONLY) for d in ALL_DISKS]
    fds_3 = fds_all[:3]
    
    # Get minimum partition size
    min_size = min(os.lseek(fd, 0, os.SEEK_END) for fd in fds_all)
    print(f"Minimum partition size: {min_size} bytes ({min_size / (1024**4):.2f} TB)")

    # 1. Verify start (should be 3-disk) and near-end (should be 4-disk)
    # Skip first 128MB to avoid superblocks/boot sectors/zeros
    start_offset = 128 * 1024 * 1024
    end_offset = min_size - (128 * 1024 * 1024)
    
    p3_start = test_parity_at_offset(fds_3, start_offset)
    p4_end = test_parity_at_offset(fds_all, end_offset)
    print(f"Start (128MB) 3-disk XOR match: {p3_start:.2%}")
    print(f"End (-128MB)  4-disk XOR match: {p4_end:.2%}")

    if p3_start < 0.8 or p4_end < 0.8:
        print("WARNING: Start/End parity check inconclusive (might hit all-zero space).")
        print("Adjust start_offset/end_offset in script to active data regions.")

    # 2. Binary search for the transition point (aligned to 4KB blocks)
    low = 0
    high = min_size // BLOCK_SIZE
    
    print("\nBinary searching for reshape transition point...")
    while high - low > 64:
        mid = (low + high) // 2
        byte_pos = mid * BLOCK_SIZE
        
        # Scan forward slightly if we land in an all-zero hole
        p3 = -1.0
        p4 = -1.0
        probe_pos = byte_pos
        while probe_pos < high * BLOCK_SIZE:
            p3 = test_parity_at_offset(fds_3, probe_pos)
            p4 = test_parity_at_offset(fds_all, probe_pos)
            if p3 >= 0 and p4 >= 0:
                break
            probe_pos += 1024 * 1024 * 16  # Jump 16MB past empty space
            
        if p3 > 0.8 and p4 < 0.2:
            low = probe_pos // BLOCK_SIZE
        elif p4 > 0.8 and p3 < 0.2:
            high = mid
        else:
            print(f"Ambiguous zone at {byte_pos}: p3={p3:.2f}, p4={p4:.2f}")
            break

    print(f"\nTransition zone narrowed to bytes: {low * BLOCK_SIZE} -> {high * BLOCK_SIZE}")
    print("Run a fine-grained scan in this 256KB window to find the exact stripe boundary.")

if __name__ == "__main__":
    main()
