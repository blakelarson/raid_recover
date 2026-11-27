# 1. Format ONLY /dev/sdc5 (NEVER /dev/sdc!) with ext4 (-m 0 so all 5.45 TiB is usable)
sudo mkfs.ext4 -m 0 -L extra_5tb /dev/sdc5

# 2. Mount /dev/sdc5
sudo mkdir -p /mnt/sdc5_extra
sudo mount /dev/sdc5 /mnt/sdc5_extra
df -h /mnt/sdc5_extra

# 3. Copy DriveImages (2.9T) and ProbablyDuplicates (2.2T) to /mnt/sdc5_extra
sudo rsync -aHAX --info=progress2 \
    /mnt/recovery/lv_backups_old/DriveImages \
    /mnt/recovery/lv_backups_old/ProbablyDuplicates \
    /mnt/sdc5_extra/
