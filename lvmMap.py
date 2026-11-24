#!/usr/bin/env python3
import os

fd = os.open("/dev/sda4", os.O_RDONLY)
os.lseek(fd, 135266304, os.SEEK_SET)  # 129.0000 MB
buf = os.read(fd, 131072)  # Read 128KB of LVM metadata area
os.close(fd)

# Extract all printable ASCII blocks > 20 chars
import re
for m in re.finditer(b'[\x20-\x7e\n\t]{40,}', buf):
    print(m.group(0).decode('ascii'))
    print("=" * 50)
