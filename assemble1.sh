# 1. Re-assemble your other working RAID arrays (md0 and md2) read-only
sudo mdadm --assemble --scan --readonly
cat /proc/mdstat

# 2. Scan all Physical Volumes (md0, md1, md2) and activate vg_main
sudo pvscan --cache
sudo pvdisplay
sudo vgchange -ay --partial vg_main
sudo lvs -a -o +devices
