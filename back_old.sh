# 1. List top-level directories and modification dates in lv_backups_old
ls -la /mnt/recovery/lv_backups_old

# 2. Check top-level directory sizes (runs fast for top-level folders)
sudo du -sh /mnt/recovery/lv_backups_old/* 2>/dev/null
