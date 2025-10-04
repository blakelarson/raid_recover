# RAID Recovery

I botched my RAID. Trying to re-assemble it by hand. This may be a fool's errand!

# TODOS

## Metadata
Need to accomodate RAID metadata at beginning of sources maybe? Not sure how to get this going. Perhaps "search" for next 512 bytes (1 sector) of properly xor-ed data then using that to take a 64k chunk. 

## Parity
Good news is that xor will confim a little, but we can't tell which drive is the parity one for a particular chunk. Might be worth checking out raid github depo.

