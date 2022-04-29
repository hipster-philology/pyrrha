#!/bin/sh
set -ex
wget -N https://chromedriver.storage.googleapis.com/101.0.4951.41/chromedriver_linux64.zip -P ~/
unzip ~/chromedriver_linux64.zip -d ~/
rm ~/chromedriver_linux64.zip
sudo mv -f ~/chromedriver /usr/local/share/
sudo chmod +x /usr/local/share/chromedriver
sudo rm /usr/local/bin/chromedriver || echo "Nothing to remove"
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver