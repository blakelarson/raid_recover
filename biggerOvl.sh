# 1. Check free RAM in /dev/shm first (you have ~7.8 GB free from your screenshot)
df -h /dev/shm

# 2. Expand each 16MB backing file to 512MB and tell the loop device + dmsetup snapshot to grow
for dev in sda4 sdb5 sdd5 sde4; do
    LOOP=$(losetup -j /dev/shm/ovl_${dev} | cut -d: -f1)
    sudo truncate -s 512M /dev/shm/ovl_${dev}
    sudo losetup -c "$LOOP"
    SECTORS=$(sudo blockdev --getsz /dev/${dev})
    sudo dmsetup suspend ovl_${dev}
    echo "0 ${SECTORS} snapshot /dev/${dev} ${LOOP} P 8" | sudo dmsetup reload ovl_${dev}
    sudo dmsetup resume ovl_${dev}
done

# 3. Verify the second number jumped from 32768 to 1048576 (512 MB)
sudo dmsetup status | grep ovl_
