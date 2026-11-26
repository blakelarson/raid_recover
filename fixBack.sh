# 1. Attach the image to a loop device so XFS sees proper block geometry
LOOP_DEV=$(sudo losetup --find --show /mnt/new18tb/lv_backups.img)
echo "Attached to $LOOP_DEV"

# 2. Mount read-write briefly to replay the XFS journal log, then unmount
sudo mkdir -p /mnt/test_xfs
sudo mount "$LOOP_DEV" /mnt/test_xfs
df -h /mnt/test_xfs
ls -la /mnt/test_xfs
sudo umount /mnt/test_xfs

# 3. Run xfs_repair on the loop device now that the journal is clean
sudo xfs_repair "$LOOP_DEV"

# 4. Detach the loop device when finished
sudo losetup -d "$LOOP_DEV"
