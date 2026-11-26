# 1. Unmount lv_home and lv_root
sudo umount /mnt/recovery/lv_home /mnt/recovery/lv_root

# 2. Replay ext4 journals and fix inodes in RAM ONLY
sudo fsck.ext4 -y /dev/vg_main/lv_home
sudo fsck.ext4 -y /dev/vg_main/lv_root

# 3. Check how much RAM overlay space fsck used
sudo dmsetup status | grep ovl_

# 4. Remount read-only and run rsync to grab the newly recovered files
sudo mount -o ro /dev/vg_main/lv_home /mnt/recovery/lv_home
sudo mount -o ro /dev/vg_main/lv_root /mnt/recovery/lv_root

sudo rsync -aHAX --info=progress2 /mnt/recovery/lv_home/ /mnt/new18tb/lv_home/
sudo rsync -aHAX --info=progress2 /mnt/recovery/lv_root/ /mnt/new18tb/lv_root/
