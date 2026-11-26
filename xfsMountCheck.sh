# 1. See all currently attached loop devices
sudo losetup -a

# 2. Attach lv_backups.img if not already listed above, and store the exact path
LOOP_DEV=$(sudo losetup -j /mnt/new18tb/lv_backups.img | cut -d: -f1 | head -n 1)
if [ -z "$LOOP_DEV" ]; then
    LOOP_DEV=$(sudo losetup --find --show /mnt/new18tb/lv_backups.img)
fi
echo "Using loop device: $LOOP_DEV"

# 3. Verify superblock & mount
sudo xfs_repair "$LOOP_DEV"
sudo mkdir -p /mnt/test_xfs
sudo mount "$LOOP_DEV" /mnt/test_xfs
df -h /mnt/test_xfs
ls -la /mnt/test_xfs
