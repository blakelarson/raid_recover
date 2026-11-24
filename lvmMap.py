#!/usr/bin/env python3
import os

fd = os.open("/dev/sda4", os.O_RDONLY)
os.lseek(fd, 135266304, os.SEEK_SET)  # 129.0000 MB
buf = os.read(fd, 65536)  # Read first 64KB
os.close(fd)

start = buf.find(b'contents = "Text Format Volume Group"')
end = buf.find(b'\x00', start)
print(buf[start:end].decode('ascii', errors='replace'))
