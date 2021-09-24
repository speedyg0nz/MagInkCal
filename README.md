# MagInkCal
This repo contains the code needed to drive an E-Ink Magic Calendar that uses a battery powered (PiSugar2) Raspberry Pi Zero WH to retrieve events from a Google Calendar, format it into the desired layout, before pushing it to a Waveshare 12.48" tri-color E-Ink display. Note that the code has only been tested on the specific hardware mentioned, and customization of the code is necessary for it to work with other E-Ink displays or Battery/RTC add-ons. That said, enjoy working on your project and hopefully this helps to jump-start your magic calendar journey.

## Background
Back in 2019, I [started a thread in Reddit](https://www.reddit.com/r/RASPBERRY_PI_PROJECTS/comments/dzveio/seeking_advice_on_wallmounted_battery_powered/) to bounce an idea I had with the community: to replicate the [Android Magic Calendar concept](https://www.youtube.com/watch?v=2KDkFgOHZ5I) that inspired many DIY projects in the years that followed. But specifically, I wanted it to run on battery so I could position it anywhere in house, and even hang it on the wall without a wire dangling beneath it. I also wanted the parts to be plug and play since I have neither the desire nor the steady hands needed to solder anything. After sitting on that idea for close to a year, I finally got my act together to order the parts I needed for this project. I [posted another update to Reddit in 2020](https://www.reddit.com/r/raspberry_pi/comments/k1hm7a/work_in_progress_1248_eink_magic_calendar_details/), but got overwhelmed with life/work so it took me almost another year before posting the full set of instructions and code here.

## Hardware Required
- [Raspberry Pi Zero WH](https://www.raspberrypi.org/blog/zero-wh/) - Header pins are needed to connect to the E-Ink display
- [Waveshare 12.48" Tri-color E-Ink Display](https://www.waveshare.com/product/12.48inch-e-paper-module-b.htm) - Unfortunately out of stock at the time this is published
- [PiSugar2 for Raspberry Pi Zero](https://www.pisugar.com/) ([Tindie](https://www.tindie.com/products/pisugar/pisugar2-battery-for-raspberry-pi-zero/)) - Highly recommended, wish they had an even bigger battery though

## How It Works
Through PiSugar2's web interface, the onboard RTC would trigger the RPi to boot up the RPi daily at 6AM. Upon boot, a cronjob on the RPi is triggered to run a Python script that fetches calendar events from Google Calendar for the next few weeks, and formats them into the desired layout before displaying it on the E-Ink display. The RPi then shuts down to conserve battery. The calendar remains displayed on the E-Ink screen, because well, E-Ink...

Some features of the calendar: 
- Since I had the luxury of using red for the display, I used it to highlight the current date, as well as recently added/updated events.
- I don't like having long bars that span across multiple days for multi-day events, so I chose to display only the start and end dates for those events, and adding small left/right arrows accordingly,
- Given limited space (oh why are large E-Ink screens still so expensive!) and resolution on the display, I could only show 3 events per day and an indicator (e.g. 4 more) for those not displayed 
- The calendar always starts from the current week, and displays the next four (total 35 days). If the dates cross over to the new month, it's displayed in grey instead of black.

## Setting Up Raspberry Pi Zero

1. Starting by flashing [Raspberrypi OS Lite](https://www.raspberrypi.org/software/operating-systems/) to a MicroSD Card.

2. After setting up the OS, run the following commmand in Terminal, and use the [raspi-config](https://www.raspberrypi.org/documentation/computers/configuration.html) interface to setup Wifi connection, enable SSH, I2C, SPI, and set the timezone to your location.

```bash
sudo raspi-config
```
3. Run the following commands in Terminal to setup the environment to run the Python scripts.

```bash
sudo apt update
sudo apt-get install python3-pip
sudo apt-get install chromium-chromedriver
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

4. Run the following commands in Terminal to install the libraries needed to drive the E-Ink display. See [this page](https://www.waveshare.com/wiki/12.48inch_e-Paper_Module) for more details.
```bash
sudo apt-get install python3-pil
sudo pip3 install RPi.GPIO
sudo pip3 install spidev
```

5. Run the following commands in Terminal to install the web interface for PiSugar2 display. See [this page](https://github.com/PiSugar/PiSugar/wiki/PiSugar2) for more details. After running the command, you would be able to access the web interface at http://<your raspberry ip>:8421 in your browser. From there you should be able specify when you wish to schedule the PiSugar2 boot up your RPi.
```bash
curl http://cdn.pisugar.com/release/Pisugar-power-manager.sh | sudo bash
```

6. Download the over the files in this repo to a folder in your PC first. 

7. In order for you to access your Google Calendar events, it's necessary to first grant the access. Follow the instructions here to get the credentials.json file from your Google API. Don't worry, take your time. I'll be waiting here.

8. Once done, copy the credentials.json file to the "gcal" folder in this project. Run the following command on your PC. A web browser should appear, asking you to grant access to your calendar. Once done, you should see a "token.pickle" file in your "gcal" folder.

```bash
python3 quickstart.py
```

9. Copy all the files over to your RPi using your preferred means. 

10. Run the following command to open crontab.
```bash
crontab -e
```
11. Specifically, add the following command to crontab so that the MagInkCal Python script runs each time the RPi is booted up.
```bash
@reboot cd /location/to/your/maginkcal && python3 maginkcal.py
```

12. That's all! Your Magic Calendar should now be refreshed at the time interval that you specified in the PiSugar2 web interface! I realize that the instructions above may not be complete, especially when it comes to the Python libraries to be installed, so feel free to ping me if you noticed anything missing.

## Acknowledgements
- [Quattrocento Font](https://fonts.google.com/specimen/Quattrocento): Font used for the calendar display
- [Bootstrap Calendar CSS](https://bootstrapious.com/p/bootstrap-calendar): Stylesheet that adapted heavily for the calendar display


## Contributing
Honestly, I probably won't be updating this code much, since it's working well for me. Nevertheless, feel free to fork and modify it for your purpose.
