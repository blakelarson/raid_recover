# 1. Check partition layout, filesystem types, UUIDs, and current mount points
lsblk -f /dev/sdf

# 2. Check for hidden RAID (mdadm) or LVM headers on any sdf partition
sudo blkid /dev/sdf*
sudo mdadm --examine /dev/sdf* 2>/dev/null || true
sudo pvs /dev/sdf* 2>/dev/null || true
