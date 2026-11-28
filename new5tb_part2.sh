sudo mkdir -p /mnt/new18tb/lv_backups_old/ProbablyDuplicates_part2

sudo rsync -aHAX --info=progress2 \
    --compare-dest=/mnt/sdc5_extra/ProbablyDuplicates/ \
    /mnt/recovery/lv_backups_old/ProbablyDuplicates/ \
    /mnt/new18tb/lv_backups_old/ProbablyDuplicates_part2/
