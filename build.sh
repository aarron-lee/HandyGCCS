#!/bin/bash
./remove.sh
python -m build --wheel --no-isolation
sudo python -m installer dist/*.whl
sudo cp -r usr/ /
sudo rm /usr/bin/handycon
sudo ln /usr/local/bin/handycon /usr/bin/handycon
sudo systemd-hwdb update
sudo udevadm control -R
sudo systemctl disable handycon.service
sleep 1
sudo systemctl stop handycon.service
sleep 1 
sudo systemctl daemon-reload
sleep 1 
sudo systemctl enable handycon.service
sleep 1
sudo systemctl restart handycon.service
sleep 3
sudo systemctl status handycon.service