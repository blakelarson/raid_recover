# 1. Attach lv_backups.img to a fresh loop device
LOOP_DEV=$(sudo losetup --find --show /mnt/new18tb/lv_backups.img)
echo "Attached to $LOOP_DEV"

# 2. Zero the dirty journal log and repair the XFS filesystem
sudo xfs_repair -L "$LOOP_DEV"

# 3. Mount read-only and verify your UrBackup files
sudo mkdir -p /mnt/test_xfs
sudo mount -o ro "$LOOP_DEV" /mnt/test_xfs
df -h /mnt/test_xfs
ls -la /mnt/test_xfs

# 4. Unmount and detach cleanly when verified
sudo umount /mnt/test_xfs
sudo losetup -d "$LOOP_DEV"
