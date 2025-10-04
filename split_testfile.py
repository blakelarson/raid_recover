from random import randbytes

chunksize = 65536

with open('test_source.bytes', 'rb') as infile:
	inbytes = bytes(infile.read())


f_array = []
f_array.append( open('testpart1.bytes', 'wb') )
f_array.append( open('testpart2.bytes', 'wb') )
f_array.append( open('testpart3.bytes', 'wb') )

num_intial_bytes = 512
for f in f_array:
	from random import randbytes
	front_bytes = randbytes( num_intial_bytes )
#	f.write(front_bytes)

read_pos = 0 	# num_intial_bytes
num_devs = len(f_array)
dev_parity_index = num_devs-1	# start with final one
while read_pos < len(inbytes):
	xor_data = bytes(chunksize) # makes blank chunk to start with
	for i in range(num_devs):
		if i != dev_parity_index:
			read_data = inbytes[read_pos:read_pos+chunksize]
			len_diff = chunksize - len(read_data)
			if len(read_data) < chunksize:
				print(f'read {len(read_data)}')
			read_data += b'\0'*len_diff
			f_array[i].write(read_data)
			print(f'XOR-ing {len(xor_data)} bytes with {len(xor_data)} bytes from device {i}')
			xor_data = bytes(x ^ y for x, y in zip(xor_data, read_data))
			read_pos += chunksize
	print(f'Writing parity chunk to device {dev_parity_index}')
	f_array[dev_parity_index].write(xor_data)
	dev_parity_index -= 1
	if dev_parity_index < 0:
		dev_parity_index = num_devs-1
	
'''
dev_index = 0
num_devs = len(f_array)
while read_pos < len(inbytes):
	xor_data = bytes(chunksize) # makes blank chunk to start with
	dev_index_start = dev_index-num_devs
	dev_index_end = dev_index-2
	dev_index_parity = dev_index-1
	print(f'Start at {read_pos} bytes, xoring devices {dev_index_start} -- {dev_index_end}')
	for i in range(dev_index_start, dev_index_end+1):
		print(f'Reading input data from {read_pos}--{read_pos+chunksize-1}')
		read_data = inbytes[read_pos:read_pos+chunksize]
		len_diff = chunksize - len(read_data)
		if len(read_data) < chunksize:
			print(f'read {len(read_data)}')
		read_data += b'\0'*len_diff
		f_array[i].write(read_data)
		print(f'XOR-ing {len(xor_data)} bytes with {len(xor_data)} bytes from device {i}')
		xor_data = bytes(x ^ y for x, y in zip(xor_data, read_data))
		read_pos += chunksize
	print(f'Writing parity chunk to device {dev_index_parity}')
	f_array[dev_index_parity].write(xor_data)
	dev_index += 1
	if dev_index >= num_devs:
		dev_index = 0
'''

for f in f_array:
	f.close()
