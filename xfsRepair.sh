# 1. Zero the dirty log and repair the XFS metadata tree on the image copy
sudo xfs_repair -L /dev/loop5

# 2. Mount read-only to verify UrBackup's directory tree and files are intact
sudo mount -o ro /dev/loop5 /mnt/test_xfs
df -h /mnt/test_xfs
ls -la /mnt/test_xfs/urbackup/

# 3. Clean up the test mount and loop device when verified
sudo umount /mnt/test_xfs
sudo losetup -d /dev/loop5
