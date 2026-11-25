sudo umount /mnt/recovery/lv_backups
sudo ddrescue -S -b 4M /dev/vg_main/lv_backups /mnt/new18tb/lv_backups.img /mnt/new18tb/lv_backups.map
