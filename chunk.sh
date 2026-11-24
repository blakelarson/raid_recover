#!/bin/bash

sudo mdadm --stop --scan 2>/dev/null || true
sudo blockdev --setro /dev/sda4 /dev/sdb5 /dev/sdd5 /dev/sde4

sudo mdadm --stop /dev/md99 2>/dev/null || true
for dev in sda4 sdb5 sdd5 sde4; do
    sudo dmsetup remove ovl_${dev} 2>/dev/null || true
done
sudo losetup -D 2>/dev/null || true

for dev in sda4 sdb5 sdd5 sde4; do
    dd if=/dev/zero of=/dev/shm/ovl_${dev} bs=1M count=16 status=none
    LOOP=$(sudo losetup --find --show /dev/shm/ovl_${dev})
    SECTORS=$(sudo blockdev --getsz /dev/${dev})
    echo "0 ${SECTORS} snapshot /dev/${dev} ${LOOP} P 8" | sudo dmsetup create ovl_${dev}
done

PERMS=(
    "ovl_sda4 ovl_sde4 ovl_sdb5 ovl_sdd5"
    "ovl_sda4 ovl_sde4 ovl_sdd5 ovl_sdb5"
    "ovl_sda4 ovl_sdb5 ovl_sde4 ovl_sdd5"
    "ovl_sda4 ovl_sdb5 ovl_sdd5 ovl_sde4"
    "ovl_sda4 ovl_sdd5 ovl_sde4 ovl_sdb5"
    "ovl_sda4 ovl_sdd5 ovl_sdb5 ovl_sde4"
)

for chunk in 512 64 128 256 1024; do
    for perm in "${PERMS[@]}"; do
        DEVS=$(echo $perm | sed 's|ovl_|/dev/mapper/ovl_|g')
        sudo mdadm --stop /dev/md99 2>/dev/null || true
        sudo mdadm --create /dev/md99 --level=5 --raid-devices=4 \
            --layout=left-symmetric --chunk=${chunk} \
            --data-offset=264192s --assume-clean --run $DEVS >/dev/null 2>&1
        
        sudo vgscan --cache >/dev/null 2>&1 || true
        sudo vgchange -ay vg_main >/dev/null 2>&1 || true
        
        INFO=$(sudo blkid /dev/vg_main/* 2>/dev/null || true)
        if [ -n "$INFO" ]; then
            echo "=== MATCH: Chunk=${chunk}K | Order: $perm ==="
            echo "$INFO"
            exit 0
        fi
        sudo vgchange -an vg_main >/dev/null 2>&1 || true
    done
done

echo "Done loop. Checking /dev/md99 status:"
cat /proc/mdstat
sudo pvdisplay /dev/md99 || true
