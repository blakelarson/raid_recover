#!/bin/bash
set -e

# 1. Stop any auto-assembled arrays and lock physical disks read-only
sudo mdadm --stop --scan || true
sudo blockdev --setro /dev/sda4 /dev/sdb5 /dev/sdd5 /dev/sde4

# 2. Clean up any previous test overlays if re-running
sudo mdadm --stop /dev/md99 2>/dev/null || true
for dev in sda4 sdb5 sdd5 sde4; do
    sudo dmsetup remove ovl_${dev} 2>/dev/null || true
done
sudo losetup -D 2>/dev/null || true

# 3. Create 16MB RAM overlays so physical disks are 100% untouched
for dev in sda4 sdb5 sdd5 sde4; do
    truncate -s 16M /dev/shm/ovl_${dev}
    LOOP=$(sudo losetup --find --show /dev/shm/ovl_${dev})
    SECTORS=$(sudo blockdev --getsz /dev/${dev})
    echo "0 ${SECTORS} snapshot /dev/${dev} ${LOOP} P 8" | sudo dmsetup create ovl_${dev}
done

# 4. Test the 6 permutations (starting with mdadm's default 512K chunk)
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
        
        sudo pvscan --cache /dev/md99 >/dev/null 2>&1 || true
        sudo vgchange -ay vg_main >/dev/null 2>&1 || true
        
        # Check if any Logical Volume in vg_main shows a valid filesystem signature via blkid
        VALID_FS=$(sudo blkid /dev/vg_main/* 2>/dev/null | grep -E "ext[234]|xfs|btrfs|swap" || true)
        if [ -n "$VALID_FS" ]; then
            echo "===================================================="
            echo "SUCCESS! Chunk=${chunk}K | Order: $perm"
            echo "$VALID_FS"
            echo "===================================================="
            exit 0
        fi
        sudo vgchange -an vg_main >/dev/null 2>&1 || true
    done
done

echo "No standard filesystem detected via blkid—check dmesg or LUKS/encryption headers on /dev/vg_main/*"
