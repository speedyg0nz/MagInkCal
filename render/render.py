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
        # print(self.htmlFile)

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

        redimg = Image.open(self.currPath + '/calendar.png')  # get image)
        pixels = redimg.load()  # create the pixel map

        for i in range(redimg.size[0]):  # for every pixel:
            for j in range(redimg.size[1]):
                if pixels[i, j][0] <= pixels[i, j][1] and pixels[i, j][0] <= pixels[i, j][2]:  # if is red
                    pixels[i, j] = (255, 255, 255)  # change to white
        redimg = redimg.rotate(self.rotateAngle, expand=True)

        blackimg = Image.open(self.currPath + '/calendar.png')  # get image)
        pixels = blackimg.load()  # create the pixel map

        for i in range(blackimg.size[0]):  # for every pixel:
            for j in range(blackimg.size[1]):
                if pixels[i, j][0] > pixels[i, j][1] and pixels[i, j][0] > pixels[i, j][2]:  # if is red
                    pixels[i, j] = (255, 255, 255)  # change to white
        blackimg = blackimg.rotate(self.rotateAngle, expand=True)

        self.logger.info('Image colours processed. Extracted grayscale and red images.')
        print('Image colours processed. Returning grayscale and red images.')

        return blackimg, redimg

    def get_day_in_cal(self, startDate, eventDate):
        delta = eventDate - startDate
        return delta.days

    def get_short_time(self, datetimeObj, is24hour=False):
        datetimeStr = ''
        if is24hour:
            datetimeStr = '{:02d}'.format(datetimeObj.hour) + ':{:02d}'.format(datetimeObj.minute)
        else:
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
        is24hour = calDict['is24hour']

        # for each item in the eventList, add them to the relevant day in our calendar list
        for event in calDict['events']:
            idx = self.get_day_in_cal(calDict['calStartDate'], event['startDatetime'].date())
            if idx >= 0:
                calList[idx].append(event)
            if event['isMultiday']:
                idx = self.get_day_in_cal(calDict['calStartDate'], event['endDatetime'].date())
                if idx < len(calList):
                    calList[idx].append(event)

        # Read html template
        with open(self.currPath + '/calendar_template.html', 'r') as file:
            calendar_template = file.read()

        # Insert month header
        month_name = str(calDict['today'].month)

        # Insert battery icon
        # batteryDisplayMode - 0: do not show / 1: always show / 2: show when battery is low
        battLevel = calDict['batteryLevel']

        if batteryDisplayMode == 0:
            battText = 'batteryHide'
        elif batteryDisplayMode == 1:
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

        elif batteryDisplayMode == 2 and battLevel < 20.0:
            battText = 'battery0'
        elif batteryDisplayMode == 2 and battLevel >= 20.0:
            battText = 'batteryHide'
        print(battLevel, battText)
        # Populate the day of week row
        cal_days_of_week = ''
        for i in range(0, 7):
            cal_days_of_week += '<li class="font-weight-bold text-uppercase">' + dayOfWeekText[
                (i + weekStartDay) % 7] + "</li>\n"

        # Populate the date and events
        cal_events_text = ''
        for i in range(len(calList)):
            currDate = calDict['calStartDate'] + timedelta(days=i)
            dayOfMonth = currDate.day
            if currDate == calDict['today']:
                cal_events_text += '<li><div class="datecircle">' + str(dayOfMonth) + '</div>\n'
            elif currDate.month != calDict['today'].month:
                cal_events_text += '<li><div class="date text-muted">' + str(dayOfMonth) + '</div>\n'
            else:
                cal_events_text += '<li><div class="date">' + str(dayOfMonth) + '</div>\n'

            for j in range(min(len(calList[i]), maxEventsPerDay)):
                event = calList[i][j]
                cal_events_text += '<div class="event'
                if event['isUpdated']:
                    cal_events_text += ' text-danger'
                elif currDate.month != calDict['today'].month:
                    cal_events_text += ' text-muted'
                if event['isMultiday']:
                    if event['startDatetime'].date() == currDate:
                        cal_events_text += '">►' + event['summary']
                    else:
                        # calHtmlList.append(' text-multiday">')
                        cal_events_text += '">◄' + event['summary']
                elif event['allday']:
                    cal_events_text += '">' + event['summary']
                else:
                    cal_events_text += '">' + self.get_short_time(event['startDatetime'], is24hour) + ' ' + event[
                        'summary']
                cal_events_text += '</div>\n'
            if len(calList[i]) > maxEventsPerDay:
                cal_events_text += '<div class="event text-muted">' + str(len(calList[i]) - maxEventsPerDay) + ' more'

            cal_events_text += '</li>\n'

        # Append the bottom and write the file
        htmlFile = open(self.currPath + '/calendar.html', "w")
        htmlFile.write(calendar_template.format(month=month_name, battText=battText, dayOfWeek=cal_days_of_week,
                                                events=cal_events_text))
        htmlFile.close()

        calBlackImage, calRedImage = self.get_screenshot()

        return calBlackImage, calRedImage
