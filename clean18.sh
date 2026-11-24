sudo wipefs -a /dev/sdf
sudo parted -s /dev/sdf mklabel gpt mkpart primary ext4 0% 100%
sudo partprobe /dev/sdf
sudo mkfs.ext4 -m 0 -L recovery_18tb /dev/sdf1

sudo mkdir -p /mnt/new18tb
sudo mount /dev/sdf1 /mnt/new18tb
df -h /mnt/new18tb
