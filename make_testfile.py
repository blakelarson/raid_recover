from random import randbytes

chunk_size = 65536
num_bytes = 600*chunk_size

all_bytes = randbytes( num_bytes )

with open('test_source.bytes', 'wb') as f:
	f.write(all_bytes)


