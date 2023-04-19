# MagInkCal
This repo contains the code needed to drive an E-Ink Magic Calendar that uses a battery powered (PiSugar2) Raspberry Pi Zero WH to retrieve events from a Google Calendar, format it into the desired layout, before pushing it to a Waveshare 12.48" tri-color E-Ink display. Note that the code has only been tested on the specific hardware mentioned, and customization of the code is necessary for it to work with other E-Ink displays or Battery/RTC add-ons. That said, enjoy working on your project and hopefully this helps to jump-start your magic calendar journey.

![20210924_175459](https://user-images.githubusercontent.com/5581989/134661608-bac1f0bf-e7e3-41fe-b92e-37c26dad8fbe.jpg)


## Background
Back in 2019, I [started a thread in Reddit](https://www.reddit.com/r/RASPBERRY_PI_PROJECTS/comments/dzveio/seeking_advice_on_wallmounted_battery_powered/) to bounce an idea I had with the community: to replicate the [Android Magic Calendar concept](https://www.youtube.com/watch?v=2KDkFgOHZ5I) that inspired many DIY projects in the subsequent years. But specifically, I wanted it to run on battery so I could position it anywhere in house, and even hang it on the wall without a wire dangling beneath it. I also wanted the parts to be plug and play since I had neither the desire nor the steady hands needed to solder anything. After sitting on that idea for close to a year, I finally got my act together and ordered the parts I needed for this project. I [posted another update to Reddit in 2020](https://www.reddit.com/r/raspberry_pi/comments/k1hm7a/work_in_progress_1248_eink_magic_calendar_details/), but got overwhelmed with life/work so it took me almost another year before posting the full set of instructions and code here. An update was also [posted on Reddit](https://www.reddit.com/r/raspberry_pi/comments/pugv7d/maginkcal_magic_calendar_project_completed_full/) to share this with the community.

## Hardware Required
- [Raspberry Pi Zero WH](https://www.raspberrypi.org/blog/zero-wh/) - Header pins are needed to connect to the E-Ink display
- [Waveshare 12.48" Tri-color E-Ink Display](https://www.waveshare.com/product/12.48inch-e-paper-module-b.htm) - Unfortunately out of stock at the time this was published in September 2021
- [PiSugar2 for Raspberry Pi Zero](https://www.pisugar.com/) ([Tindie](https://www.tindie.com/products/pisugar/pisugar2-battery-for-raspberry-pi-zero/)) - Provides the RTC and battery for this project

**Update (22 Nov 2022)**: Looks like the 12.48" E-Ink Display is finally back in stock over at Waveshare! And a [new version of the PiSugar](https://www.tindie.com/products/pisugar/pisugar3-battery-for-raspberry-pi-zero/) with USB-C port has been released over the past year as well.

## How It Works
Through PiSugar2's web interface, the onboard RTC can be set to wake and trigger the RPi to boot up daily at a time of your preference. Upon boot, a cronjob on the RPi is triggered to run a Python script that fetches calendar events from Google Calendar for the next few weeks, and formats them into the desired layout before displaying it on the E-Ink display. The RPi then shuts down to conserve battery. The calendar remains displayed on the E-Ink screen, because well, E-Ink...

Some features of the calendar: 
- Battery life is the big question so I'll address it first. I'm getting around 3-4 weeks before needing to recharge the PiSugar2. I'm fairly happy with this but I'm sure this can be extended if I optimize the code further.
- Since I had the luxury of using red for the E-Ink display, I used it to highlight the current date, as well as recently added/updated events.
- I don't like having long bars that span across multiple days for multi-day events, so I chose to display only the start and end dates for those events, and adding small left/right arrows accordingly,
- Given limited space (oh why are large E-Ink screens still so expensive!) and resolution on the display, I could only show 3 events per day and an indicator (e.g. 4 more) for those not displayed 
- The calendar always starts from the current week, and displays the next four (total 35 days). If the dates cross over to the new month, it's displayed in grey instead of black.

![MagInkCal Basics](https://user-images.githubusercontent.com/5581989/134775456-d6bacaca-03c7-4357-af28-7c06aa19ed90.png)

## Setting Up Raspberry Pi Zero

1. Start by flashing [Raspberrypi OS Lite](https://www.raspberrypi.org/software/operating-systems/) to a MicroSD Card. (March 2023 Edit: If you're still using the original Raspberry Pi Zero, there are [known issues](https://forums.raspberrypi.com/viewtopic.php?t=323478) between the latest RPiOS "bullseye" release and chromium-browser, which is required to run this code. As such, I would recommend that you keep to the legacy "buster" OS if you're still running this on older RPiO hardware.)

2. After setting up the OS, run the following commmand in the RPi Terminal, and use the [raspi-config](https://www.raspberrypi.org/documentation/computers/configuration.html) interface to setup Wifi connection, enable SSH, I2C, SPI, and set the timezone to your location.

```bash
sudo raspi-config
```
3. Run the following commands in the RPi Terminal to setup the environment to run the Python scripts.

```bash
sudo apt update
sudo apt-get install python3-pip
sudo apt-get install chromium-chromedriver
sudo apt-get install libopenjp2-7-dev
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip3 install pytz
pip3 install selenium
pip3 install Pillow
```

4. Run the following commands in the RPi Terminal to install the libraries needed to drive the E-Ink display. See [this page](https://www.waveshare.com/wiki/12.48inch_e-Paper_Module) for more details.
```bash
sudo apt-get install python3-pil
sudo pip3 install RPi.GPIO
sudo pip3 install spidev
sudo apt-get install wiringpi
```

5. Run the following commands in the RPi Terminal to install the web interface for PiSugar2 display. See [this page](https://github.com/PiSugar/PiSugar/wiki/PiSugar2) for more details. After running the command, you would be able to access the web interface at http://your_raspberry_ip:8421 in your browser. From there you should be able to specify when you wish to schedule the PiSugar2 boot up your RPi.
```bash
curl http://cdn.pisugar.com/release/Pisugar-power-manager.sh | sudo bash
```

6. Download the over the files in this repo to a folder in your PC first. 

7. In order for you to access your Google Calendar events, it's necessary to first grant the access. Follow the [instructions here](https://developers.google.com/calendar/api/quickstart/python) on your PC to get the credentials.json file from your Google API. Don't worry, take your time. I'll be waiting here.

8. Once done, copy the credentials.json file to the "gcal" folder in this project. Run the following command on your PC. A web browser should appear, asking you to grant access to your calendar. Once done, you should see a "token.pickle" file in your "gcal" folder.

```bash
python3 quickstart.py
```

9. Copy all the files over to your RPi using your preferred means. 

10. Run the following command in the RPi Terminal to open crontab.
```bash
crontab -e
```
11. Specifically, add the following command to crontab so that the MagInkCal Python script runs each time the RPi is booted up.
```bash
@reboot cd /location/to/your/maginkcal && python3 maginkcal.py
```

12. That's all! Your Magic Calendar should now be refreshed at the time interval that you specified in the PiSugar2 web interface! 

PS: I'm aware that the instructions above may not be complete, especially when it comes to the Python libraries to be installed, so feel free to ping me if you noticed anything missing and I'll add it to the steps above.

## Acknowledgements
- [Quattrocento Font](https://fonts.google.com/specimen/Quattrocento): Font used for the calendar display
- [Bootstrap Calendar CSS](https://bootstrapious.com/p/bootstrap-calendar): Stylesheet that was adapted heavily for the calendar display
- [emagra](https://github.com/emagra): For adding in new features, such as 24hr display and multiple calendar selection. 
- [/u/aceisace](https://www.reddit.com/user/aceisace/): For the tips on E-Ink development and the [InkyCal](https://github.com/aceisace/Inkycal) repo (worth checking out even though I didn't use it for this project).   
  
## Contributing
I won't be updating this code much, since it has been serving me well. Nevertheless, feel free to fork the repo and modify it for your own purpose. At the same time, check out other similar projects, such as [InkyCal](https://github.com/aceisace/Inkycal). It's much more polished and also actively developed.

## Buy Me A Coffee
If this project has helped you in any way, do buy me a coffee so I can continue to build more of such projects in the future and share them with the community!

<a href="https://www.buymeacoffee.com/speedygonz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>


## What's Next
Honestly, the cost of this project is way too high for a single purpose device. Personally, I've been looking at E-Ink tablets that emulate the experience of writing on paper, and allow the users to take notes on the go. Those familiar with this range of products would be aware of the reMarkable tablet, Ratta Supernote, Kobo Elipsa and many others. My next project is likely to enhance one of these devices such that the calendar will be displayed when it's not in use. While this is usually possible by manually setting the sleep screen image / screensaver, I'm looking to have the screensaver updated automatically on a daily basis, like how it was done in this project.

**Edit (Apr 2023)**: So after finishing up this project, I went on to build an E-Ink Dashboard that offers rich, timely and glanceable information pulled from Google Calendar, OpenWeatherMap and ChatGPT! Find out more over at: https://github.com/speedyg0nz/MagInkDash
