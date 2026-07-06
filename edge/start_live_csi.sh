#!/bin/bash

# start_live_csi.sh
#
# Configure Nexmon CSI for real-time edge inference.
#
# This script only sets up the CSI receiving environment.
# It does NOT save pcap files.
# After running this script, start:
#
# sudo python3 edge/live_lsvm_matlab_style_publisher.py --broker 10.42.1.1 --topic csi/aerosol/pred

echo "Setting up Nexmon CSI for live inference..."

MAKECSIPARAMS_DIR="/home/pi/nexmon/patches/bcm43455c0/7_45_189/nexmon_csi/utils/makecsiparams"

cd "$MAKECSIPARAMS_DIR" || {
    echo "ERROR: Cannot enter makecsiparams directory."
    exit 1
}

CHANNEL_NUM=36
BANDWIDTH=80

# Optional MAC list used by the original Nexmon CSI setup.
# This is kept for compatibility with the original experiment environment.
if [ -f /home/pi/nexmon_csi_setup/MAC_Addr_list.sh ]; then
    source /home/pi/nexmon_csi_setup/MAC_Addr_list.sh
fi

echo "Kill wpa_supplicant..."
sudo pkill wpa_supplicant

echo "Configure Nexmon CSI params: channel ${CHANNEL_NUM}/${BANDWIDTH}"

# Core Nexmon CSI enabling command.
# This is the key command that activates CSI extraction in the Nexmon firmware.
sudo nexutil -Iwlan0 -s500 -b -l34 -v$(./makecsiparams -c ${CHANNEL_NUM}/${BANDWIDTH} -C 0x1 -N 0x1)

echo "Bring wlan0 up..."
sudo ifconfig wlan0 up
sleep 2

echo "Create monitor interface mon0 if it does not exist..."
if ! iw dev | grep -q "Interface mon0"; then
    sudo iw phy $(iw dev wlan0 info | gawk '/wiphy/ {printf "phy" $2}') interface add mon0 type monitor
fi

sudo ifconfig mon0 up
sudo ifconfig wlan0 up

echo "Live CSI setup done."
echo "To verify CSI packets:"
echo "  sudo tcpdump -i wlan0 udp port 5500 -c 5"
echo ""
echo "Then run live inference:"
echo "  sudo python3 edge/live_lsvm_matlab_style_publisher.py --broker 10.42.1.1 --topic csi/aerosol/pred"
