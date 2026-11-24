#!/usr/bin/env python3
import itertools
import os

DATA_OFFSET = 135266304  # 129.0000 MB (Sector 264192)
DISK_0 = "/dev/sda4"
OTHER_DISKS = ["/dev/sde4", "/dev/sdb5", "/dev/sdd5"]
CHUNK_SIZES_KB = [512, 64, 128, 256, 1024]

def read_virtual_raid(disks, chunk_bytes, num_chunks=12):
    """
    Reconstructs the first `num_chunks` data chunks of a 4-disk left-symmetric RAID5.
    In left-symmetric 4-disk RAID5:
      Stripe 0: D0, D1, D2, P
      Stripe 1: D1, D2, P,  D0
      Stripe 2: D2, P,  D0, D1
      Stripe 3: P,  D0, D1, D2
    """
    fds = [os.open(d, os.O_RDONLY) for d in disks]
    out = bytearray()
    stripe = 0
    while len(out) < num_chunks * chunk_bytes:
        p_idx = 3 - (stripe % 4)
        # Left-symmetric data order starts immediately after parity disk (wrapping around)
        data_indices = [(p_idx + 1 + i) % 4 for i in range(3)]
        for idx in data_indices:
            os.lseek(fds[idx], DATA_OFFSET + stripe * chunk_bytes, os.SEEK_SET)
            out.extend(os.read(fds[idx], chunk_bytes))
        stripe += 1
    for fd in fds:
        os.close(fd)
    return bytes(out)

for chunk_kb in CHUNK_SIZES_KB:
    chunk_bytes = chunk_kb * 1024
    for perm in itertools.permutations(OTHER_DISKS):
        order = [DISK_0] + list(perm)
        # Read first 1.5 MB of reconstructed virtual array
        data = read_virtual_raid(order, chunk_bytes, num_chunks=max(4, (1536 * 1024) // chunk_bytes))
        
        # Look for LVM2 metadata text ("contents = \"Text Format Volume Group\"")
        if b'Text Format Volume Group' in data:
            # Verify there is no binary corruption inside the ASCII metadata block
            start = data.find(b'contents = "Text Format Volume Group"')
            snippet = data[start:start+600]
            try:
                text = snippet.decode('ascii')
                print(f"\n[MATCH FOUND!] Chunk Size: {chunk_kb}K | Order: {' '.join(order)}")
                print("-" * 60)
                print(text[:400])
                print("-" * 60)
            except UnicodeDecodeError:
                pass
