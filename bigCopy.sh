for lv in lv_documents lv_pictures lv_home lv_music lv_videos lv_root lv_logs lv_backups; do
    echo "=== Copying ${lv} ==="
    sudo mkdir -p /mnt/new18tb/${lv}
    sudo rsync -aHAX --info=progress2 /mnt/recovery/${lv}/ /mnt/new18tb/${lv}/
done
