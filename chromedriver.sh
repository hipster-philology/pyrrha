wget -N https://chromedriver.storage.googleapis.com/81.0.4044.69/chromedriver_linux64.zip -P ~/
unzip ~/chromedriver_linux64.zip -d ~/
rm ~/chromedriver_linux64.zip
sudo mv -f ~/chromedriver /usr/local/share/
sudo chmod +x /usr/local/share/chromedriver
sudo rm /usr/local/bin/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver