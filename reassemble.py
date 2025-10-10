import argparse
import json
import logging
import os
from functools import reduce
from operator import xor
from math import ceil

# TODO: need to *not* advance parity if we are skipping

# TODO: use the searching function to just zoom up to the next parity spot
# need to check that the non-partiy chunk comes first then we zoom up to the parity.
# if the parity runs out before the end of the chunk, then we might have a problem!
# I'm guessing that any superblock or other metadata occurs between blocks. 
# perhaps we "find" the zeros to find the border (which may be approximate!)
# count(b'\x00') of a subset -- start at first half -- if there is a larger percentage
# of zeros in the second half than there are in the whole then we are on to something.
# We need 100% zeros in a final section to do an auto-skip. Everything else is
# a result that needs flagging. So maybe...
# Check if last 8 bytes or whatever are zeros (i.e. partiy checked). If so then we 
# potentially can do a skip. So we do the skip.
# Check if final half of results are zeros. If yes, then check final quarter.
# if not, check final three quarters. Put another way:
# a = 0, b = end (big search). c = (a+b)/2
# if all_zeros(c,b) then c = (a+c)/2 else c = (c+b)/2 and a = c_old 
# the "else" works because we know the left size is not all zeros
# for example, a = 0, b = 120 so c = 60
# if all_zeros(c,b) then c = (a+c/2)=30 else c = (c+b)/2 = 90 and a = 60. Say the else:
# if all_zeros(90,120) then c = 75 else a = 90 and c = 105
# WAIT -- if we only care if zeros at end, then b never changes

logging.basicConfig(level=logging.DEBUG, filename="reassemble.log")

class Device(object):
    all_fh:list = []

    def __init__(self, devpath:str, nextpos:int, size:int, flags:int = os.O_RDONLY):
        self.devpath:str = devpath
        self.nextpos:int = nextpos
        self.size:int = size
        self.fh:int = os.open(self.devpath, flags)
        self.all_fh.append( self.fh )

def xor_chunks(chunkarray:list):
    return bytes(reduce(xor, grp) for grp in zip(*chunkarray))

def readchunk(devlist:list, parity_index:int, CHUNKSIZE:int):
    chunkarray:list = []
    data_dev_list = list(range(len(devlist)))   # just all the drives
    del data_dev_list[parity_index]     # remove the parity drive
    for idx in data_dev_list: #range(num_devs):
        logging.debug(f'Reading {CHUNKSIZE} bytes from {devlist[idx].devpath} starting at {devlist[idx].nextpos}')
        chunkarray.append( os.read( devlist[idx].fh, CHUNKSIZE) )
        logging.debug(f'{len(chunkarray[-1])} bytes from data device {idx}')
    if len(chunkarray[0]) == 0:
        return b''
    parity_chunk:bytes = os.read( devlist[parity_index].fh, CHUNKSIZE )
    logging.debug(f'{len(parity_chunk)} data bytes from parity device {parity_index}')
    if xor_chunks(chunkarray) == parity_chunk:
        fullchunk:bytes = b''
        for c in chunkarray:
            fullchunk += c
        logging.debug(f'partiy check passed')
        for d in devlist:
            d.nextpos += CHUNKSIZE
        return fullchunk
    else:
        full_xor:bytes = xor_chunks(chunkarray+[parity_chunk])
        non_zero_count = len(full_xor) - full_xor.count(b'\x00')
        logging.warning(f'parity check failed. {non_zero_count} ({non_zero_count/len(full_xor):.1f}%) different bytes')
        end_zero_count = full_xor[-16:].count(b'\x00')
        logging.warning(f'end 16 bytes have parity')
        left:int = 0
        right:int = len(full_xor)
        test:int = ceil( right/2 )
        while (right-left) > 1:
            # evaluate test sample
            end_zero_count = full_xor[test:].count(b'\x00')
            size = len(full_xor) - test
            logging.debug(f'end_zero_count: {end_zero_count} \t size: {size}')
            if end_zero_count < size:
                # there are some non-zeros in the test sample
                # so the border has to be to the right of test
                left = test
                test = ceil( (test+right)/2 )
                logging.debug(f'Still have some disparity. new parameters are:\t left = {left} \t test = {test}')
            elif end_zero_count == size:
                # all in sample are zeros. Border must be to the left
                right = test
                test = ceil( (left+test)/2 )
                logging.debug(f'all in sample have parity. need to sample more. new parameters are:\t test = {test} \t right = {right}')
            else:
                raise
        logging.debug(f'solved. left = {left} and test = {test} and right = {right}.')
        for d in devlist:
            fwd:int = right - CHUNKSIZE
            logging.debug(f'Scooting forward {fwd} on device {d.devpath}')
            os.lseek(d.fh, fwd, os.SEEK_CUR)
            d.nextpos += right
        return None

def save_json(config:json, source_dev_list:list, dest_dev:Device):
    for i in range(len(source_dev_list)):
        config['source_devices'][i]['next_read_position'] = source_dev_list[i].nextpos
    config['next_write_position'] = dest_dev.nextpos
    with open("config.json", "w") as fj:
        json.dump(config, fj, indent=4 )
    logging.debug(f'Write position saved at {dest_dev.nextpos}')

def load_sources(config:json):
    source_dev_list = []
    for dev in config['source_devices']:
        file_info = os.stat(dev['devpath'])
        file_size_bytes = file_info.st_size
        source_dev_list.append(Device(dev['devpath'], dev['next_read_position'], file_size_bytes))
        os.lseek(source_dev_list[-1].fh, source_dev_list[-1].nextpos, os.SEEK_SET)

    return source_dev_list

def init_dest(config:json) -> Device:
    
    file_info = os.stat(config['dest_devpath'])
    file_size_bytes = file_info.st_size
    dest_dev = Device(config['dest_devpath'], config['next_write_position'], file_size_bytes, flags=os.O_RDWR)
    return dest_dev

def main(config:json, source_dev_list:list, dest_dev:Device):
    CHUNKSIZE = config['chunksize']

    #dev_index = 0
    parity_index = len(source_dev_list)-1
    next_json_save = 15*CHUNKSIZE
    scooted = 0
    while source_dev_list[0].nextpos <= source_dev_list[0].size: #dev_index >= 0:
        chunk = readchunk( source_dev_list, parity_index, CHUNKSIZE ) #dev_index )
        if chunk is not None:
            #scooted = 0
            if len(chunk) == 0:
                logging.warning('no more data available. Exiting')
                return
            num_bytes_written:int = os.write(dest_dev.fh, chunk)
            logging.debug(f'{num_bytes_written} bytes written')
            dest_dev.nextpos += num_bytes_written
            if dest_dev.nextpos >= next_json_save:
                save_json(config, source_dev_list, dest_dev)
            parity_index -= 1
            if parity_index < 0:
                parity_index = len(source_dev_list)-1
        else:
            pass
            # scoot forward a little and check again
            #scoot_len = 512
            #for d in source_dev_list:
            #    # need to rewind last read then scoot
            #    os.lseek(d.fh, scoot_len-CHUNKSIZE, os.SEEK_CUR)
            #    d.nextpos += scoot_len
            #scooted += scoot_len
            #logging.debug(f'Scooted forward {scoot_len} bytes (running total {scooted})')

    return
    #    dev_index += 1
    #    if dev_index >= len(source_dev_list):
    #        dev_index = 0

def get_args(config):
    parser = argparse.ArgumentParser("reassemble.py")
    parser.add_argument('--restart', action='store_true', help='Restart entire thing')
    args = parser.parse_args()

    if args.restart:
        for idx in range(len(config['source_devices'])):
            config['source_devices'][idx]['next_read_position'] = 0
        config['next_write_position'] = 0
        logging.info('restarting entire process')
    
    return config


def shutdown(config:json, source_dev_list:list, dest_dev:Device):
    save_json(config, source_dev_list, dest_dev)
    logging.debug(f'Closing all {len(Device.all_fh)} files:')
    for f in Device.all_fh:
        os.close(f)

if __name__ == "__main__":
    with open("config.json") as fj:
        config = json.load(fj)

    config = get_args(config)    

    logging.debug('--- Config Loaded ---')
    source_dev_list = load_sources(config)
    dest_dev = init_dest(config)
    main(config, source_dev_list, dest_dev)

    shutdown(config, source_dev_list, dest_dev)


#dev = os.open(source_file, os.O_RDONLY)
#os.close(dev)
#os.read(dev, )

'''
# diff <(xxd test_source.bytes) <(xxd test_dest.bytes)


def xor_chunks_old(chunkarray:list):
    if len(chunkarray) != 2:
        raise
    return bytes(x ^ y for x, y in zip(chunkarray[0], chunkarray[1]))

def readchunk_old(devlist:list, dev_index:int):
    num_devs:int = len(devlist)
    chunkarray:list = []
    dev_index_start = dev_index -num_devs
    dev_index_end:int = dev_index -2
    dev_index_parity:int = dev_index-1
    print(f'xoring devices {dev_index_start} -- {dev_index_end}')
    for i in range(dev_index_start, dev_index_end+1):
        chunkarray.append( os.read( devlist[i].fh, CHUNKSIZE ) )
    print(f'{len(chunkarray[-1])} bytes from from device {i}')
    if len(chunkarray[0]) == 0:
        return b''
    parity_chunk:bytes = os.read( devlist[dev_index_parity].fh, CHUNKSIZE )
    if xor_chunks(chunkarray) == parity_chunk:
        fullchunk:bytes = b''
        for c in chunkarray:
            fullchunk += c
        print(f'success!')
        for d in devlist:
            d.nextpos += CHUNKSIZE
        return fullchunk
    else:
        raise
	
'''
