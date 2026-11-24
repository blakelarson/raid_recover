mount | grep -E "recovery|new18tb" || echo "Nothing mounted under /mnt"
cat /proc/mdstat
sudo lvs vg_main
