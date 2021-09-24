#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot. This screenshot will then be processed
to extract the grayscale and red portions, which are then sent to the eInk display for updating.

This might sound like a convoluted way to generate the calendar, but I'm doing so mainly because (i) it's easier to
format the calendar exactly the way I want it using HTML/CSS, and (ii) I can better delink the generation of the
calendar and refreshing of the eInk display. In the future, I might choose to generate the calendar on a separate
RPi device, while using a ESP32 or PiZero purely to just retrieve the image from a file host and update the screen.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from datetime import timedelta
import pathlib
from PIL import Image
import logging

class RenderHelper:

    def __init__(self, width, height, angle):
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = 'file://' + self.currPath + '/calendar.html'
        self.imageWidth = width
        self.imageHeight = height
        self.rotateAngle = angle
        #print(self.htmlFile)

    def set_viewport_size(self, driver):
        window_size = driver.execute_script("""
            return [window.outerWidth - window.innerWidth + arguments[0],
              window.outerHeight - window.innerHeight + arguments[1]];
            """, self.imageWidth, self.imageHeight)
        driver.set_window_size(*window_size)

    def get_screenshot(self):
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars");
        driver = webdriver.Chrome(options=opts)
        self.set_viewport_size(driver)
        driver.get(self.htmlFile)
        sleep(1)
        driver.get_screenshot_as_file(self.currPath + '/calendar.png')
        driver.quit()

        self.logger.info('Screenshot captured and saved to file.')
        print('Screenshot captured. Processing colours...')

        redimg = Image.open(self.currPath + '/calendar.png') # get image)
        pixels = redimg.load() # create the pixel map

        for i in range(redimg.size[0]): # for every pixel:
            for j in range(redimg.size[1]):
                if pixels[i, j][0] <= pixels[i, j][1] and pixels[i, j][0] <= pixels[i, j][2]  :  # if is red
                    pixels[i,j] = (255, 255, 255) # change to white
        redimg = redimg.rotate(self.rotateAngle, expand=True)

        blackimg = Image.open(self.currPath + '/calendar.png') # get image)
        pixels = blackimg.load() # create the pixel map

        for i in range(blackimg.size[0]): # for every pixel:
            for j in range(blackimg.size[1]):
                if pixels[i, j][0] > pixels[i, j][1] and pixels[i, j][0] > pixels[i, j][2]:  # if is red
                    pixels[i,j] = (255, 255, 255) # change to white
        blackimg = blackimg.rotate(self.rotateAngle, expand=True)

        self.logger.info('Image colours processed. Extracted grayscale and red images.')
        print('Image colours processed. Returning grayscale and red images.')

        return blackimg, redimg


    def get_day_in_cal(self, startDate, eventDate):
        delta = eventDate - startDate
        return delta.days

    def get_short_time(self, datetimeObj):
        datetimeStr = ''
        if datetimeObj.minute > 0:
            datetimeStr = ('.{:02d}').format(datetimeObj.minute)

        if datetimeObj.hour == 0:
            datetimeStr = '12' + datetimeStr + 'am'
        elif datetimeObj.hour == 12:
            datetimeStr = '12' + datetimeStr + 'pm'
        elif datetimeObj.hour > 12:
            datetimeStr = str(datetimeObj.hour % 12) + datetimeStr + 'pm'
        else:
            datetimeStr = str(datetimeObj.hour) + datetimeStr + 'am'
        return datetimeStr

    def process_inputs(self, calDict):
        # calDict = {'events': eventList, 'calStartDate': calStartDate, 'today': currDate, 'lastRefresh': currDatetime, 'batteryLevel': batteryLevel}
        # first setup list to represent the 5 weeks in our calendar
        calList = []
        for i in range(35):
            calList.append([])

        # retrieve calendar configuration
        maxEventsPerDay = calDict['maxEventsPerDay']
        batteryDisplayMode = calDict['batteryDisplayMode']
        dayOfWeekText = calDict['dayOfWeekText']
        weekStartDay = calDict['weekStartDay']

        # for each item in the eventList, add them to the relevant day in our calendar list
        for event in calDict['events']:
            idx = self.get_day_in_cal(calDict['calStartDate'], event['startDatetime'].date())
            if idx >= 0:
                calList[idx].append(event)
            if event['isMultiday']:
                idx = self.get_day_in_cal(calDict['calStartDate'], event['endDatetime'].date())
                if idx < len(calList):
                    calList[idx].append(event)

        # Read in the HTML segments for the top and bottom
        with open(self.currPath + '/calendar_top.html', 'r') as file:
            calTopHtmlStr = file.read()

        with open(self.currPath + '/calendar_bottom.html', 'r') as file:
            calBottomHtmlStr = file.read()

        # Insert month header
        calHtmlList = [calTopHtmlStr, str(calDict['today'].month), '</h2></div>']

        # Insert battery icon
        # batteryDisplayMode - 0: do not show / 1: always show / 2: show when battery is low
        if batteryDisplayMode > 0:
            battLevel = calDict['batteryLevel']
            battText = ''
            if battLevel >= 80:
                battText = 'battery80'
            elif battLevel >= 60:
                battText = 'battery60'
            elif battLevel >= 40:
                battText = 'battery40'
            elif battLevel >= 20:
                battText = 'battery20'
            else:
                battText = 'battery0'

            if batteryDisplayMode == 1 or battText == 'battery0':
                # Only display if batteryDisplayMode is set to "always show" or "show when battery is low"
                calHtmlList.append('<div class="batt_container"><img class="')
                calHtmlList.append(battText)
                calHtmlList.append('" src="battery.png" /></div>')

        # Populate the day of week row
        calHtmlList.append('<ol class="day-names list-unstyled text-center">')
        for i in range (0,7):
            calHtmlList.append('<li class="font-weight-bold text-uppercase">')
            calHtmlList.append(dayOfWeekText[(i + weekStartDay) % 7])
            calHtmlList.append('</li>')
        calHtmlList.append('</ol><ol class="days list-unstyled">')

        # Populate the date and events
        for i in range(len(calList)):
            currDate = calDict['calStartDate'] + timedelta(days=i)
            dayOfMonth = currDate.day
            if currDate == calDict['today']:
                calHtmlList.append('<li><div class="datecircle">' + str(dayOfMonth) + '</div>')
            elif currDate.month != calDict['today'].month:
                calHtmlList.append('<li><div class="date text-muted">' + str(dayOfMonth) + '</div>')
            else:
                calHtmlList.append('<li><div class="date">' + str(dayOfMonth) + '</div>')

            for j in range(min(len(calList[i]), maxEventsPerDay)):
                event = calList[i][j]
                calHtmlList.append('<div class="event')
                if event['isUpdated']:
                    calHtmlList.append(' text-danger')
                elif currDate.month != calDict['today'].month:
                    calHtmlList.append(' text-muted')
                if event['isMultiday']:
                    if event['startDatetime'].date() == currDate:
                        calHtmlList.append('">►'+event['summary'])
                    else:
                        #calHtmlList.append(' text-multiday">')
                        calHtmlList.append('">◄' + event['summary'])
                elif event['allday']:
                    calHtmlList.append('">' + event['summary'])
                else:
                    calHtmlList.append('">' + self.get_short_time(event['startDatetime']) + ' ' + event['summary'])
                calHtmlList.append('</div>\n')
            if len(calList[i]) > maxEventsPerDay:
                calHtmlList.append('<div class="event text-muted">' + str(len(calList[i])-maxEventsPerDay) + ' more')

            calHtmlList.append('</li>\n')

        # Append the bottom and write the file
        calHtmlList.append(calBottomHtmlStr)
        calHtml = ''.join(calHtmlList)
        htmlFile = open(self.currPath + '/calendar.html', "w")
        htmlFile.write(calHtml)
        htmlFile.close()

        calBlackImage, calRedImage = self.get_screenshot()

        return calBlackImage, calRedImage