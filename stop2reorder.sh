#!/bin/bash

# 1. Deactivate partial vg_main and stop the stale auto-assembled md1 / md127
sudo vgchange -an vg_main 2>/dev/null || true
sudo mdadm --stop /dev/md1 2>/dev/null || true
sudo mdadm --stop /dev/md127 2>/dev/null || true
sudo mdadm --stop /dev/md99 2>/dev/null || true

# 2. Verify overlays exist (recreate cleanly if needed)
for dev in sda4 sdb5 sdd5 sde4; do
    sudo dmsetup remove ovl_${dev} 2>/dev/null || true
done
sudo losetup -D 2>/dev/null || true
sudo blockdev --setro /dev/sda4 /dev/sdb5 /dev/sdd5 /dev/sde4

for dev in sda4 sdb5 sdd5 sde4; do
    dd if=/dev/zero of=/dev/shm/ovl_${dev} bs=1M count=16 status=none
    LOOP=$(sudo losetup --find --show /dev/shm/ovl_${dev})
    SECTORS=$(sudo blockdev --getsz /dev/${dev})
    echo "0 ${SECTORS} snapshot /dev/${dev} ${LOOP} P 8" | sudo dmsetup create ovl_${dev}
done

# Immediately stop udev from auto-assembling stale md1/md127 on the new overlays
sleep 1
sudo mdadm --stop /dev/md1 2>/dev/null || true
sudo mdadm --stop /dev/md127 2>/dev/null || true

# 3. Test the 6 disk orders with data-offset=264192s (129.0000 MB) and chunk=512K
PERMS=(
    "ovl_sda4 ovl_sde4 ovl_sdb5 ovl_sdd5"
    "ovl_sda4 ovl_sde4 ovl_sdd5 ovl_sdb5"
    "ovl_sda4 ovl_sdb5 ovl_sde4 ovl_sdd5"
    "ovl_sda4 ovl_sdb5 ovl_sdd5 ovl_sde4"
    "ovl_sda4 ovl_sdd5 ovl_sde4 ovl_sdb5"
    "ovl_sda4 ovl_sdd5 ovl_sdb5 ovl_sde4"
)

for perm in "${PERMS[@]}"; do
    DEVS=$(echo $perm | sed 's|ovl_|/dev/mapper/ovl_|g')
    sudo mdadm --stop /dev/md99 2>/dev/null || true
    sudo mdadm --create /dev/md99 --level=5 --raid-devices=4 \
        --layout=left-symmetric --chunk=512 \
        --data-offset=264192s --assume-clean --run $DEVS >/dev/null 2>&1

    sudo pvscan --cache /dev/md99 >/dev/null 2>&1 || true
    sudo vgchange -ay vg_main >/dev/null 2>&1 || true

    # Check if lv_pictures (which starts at extent 0 of pv2!) has a valid filesystem
    FS=$(sudo blkid /dev/vg_main/lv_pictures /dev/vg_main/lv_documents /dev/vg_main/lv_home 2>/dev/null || true)
    if [ -n "$FS" ]; then
        echo "===================================================="
        echo "SUCCESS! Exact 4-disk order: $perm"
        echo "$FS"
        echo "===================================================="
        sudo lvs -a -o +devices
        exit 0
    fi
    sudo vgchange -an vg_main >/dev/null 2>&1 || true
done

echo "Testing other chunk sizes (64, 128, 256)..."
for chunk in 64 128 256; do
    for perm in "${PERMS[@]}"; do
        DEVS=$(echo $perm | sed 's|ovl_|/dev/mapper/ovl_|g')
        sudo mdadm --stop /dev/md99 2>/dev/null || true
        sudo mdadm --create /dev/md99 --level=5 --raid-devices=4 \
            --layout=left-symmetric --chunk=${chunk} \
            --data-offset=264192s --assume-clean --run $DEVS >/dev/null 2>&1
        sudo pvscan --cache /dev/md99 >/dev/null 2>&1 || true
        sudo vgchange -ay vg_main >/dev/null 2>&1 || true
        FS=$(sudo blkid /dev/vg_main/lv_pictures /dev/vg_main/lv_documents /dev/vg_main/lv_home 2>/dev/null || true)
        if [ -n "$FS" ]; then
            echo "===================================================="
            echo "SUCCESS! Chunk=${chunk}K | Exact 4-disk order: $perm"
            echo "$FS"
            echo "===================================================="
            sudo lvs -a -o +devices
            exit 0
        fi
        sudo vgchange -an vg_main >/dev/null 2>&1 || true
    done
done
