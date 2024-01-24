#!/bin/sh
set -ex
# Use your CHROME version to find the URI https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_120.0.6099
wget -N https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/120.0.6099.109/linux64/chromedriver-linux64.zip -P ~/
unzip ~/chromedriver-linux64.zip -d ~/
rm ~/chromedriver-linux64.zip
sudo mv -f ~/chromedriver-linux64/chromedriver /usr/local/share/
sudo chmod +x /usr/local/share/chromedriver
sudo rm /usr/local/bin/chromedriver || echo "Nothing to remove"
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver