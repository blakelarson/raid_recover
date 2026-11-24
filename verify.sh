# 1. Check all 9 filesystems
sudo blkid /dev/vg_main/*

# 2. Create mount points and mount every volume read-only (noload prevents journal replay writes)
for lv in lv_pictures lv_documents lv_home lv_music lv_videos lv_logs lv_root lv_backups lv_backups_old; do
    sudo mkdir -p /mnt/recovery/${lv}
    sudo mount -o ro,noload /dev/vg_main/${lv} /mnt/recovery/${lv}
done

# 3. Verify used/free space across all mounted volumes
df -h /mnt/recovery/*
