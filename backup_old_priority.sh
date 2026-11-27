sudo mkdir -p /mnt/new18tb/lv_backups_old

sudo rsync -aHAX --info=progress2 \
    --exclude='DriveImages/' \
    --exclude='ProbablyDuplicates/' \
    --exclude='urbackup/' \
    --exclude='lost+found/' \
    /mnt/recovery/lv_backups_old/ /mnt/new18tb/lv_backups_old/
