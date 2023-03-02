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
from selenium.webdriver.common.by import By
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

    def set_viewport_size(self, driver):

        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html = driver.find_element(By.TAG_NAME,'html')
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = self.imageWidth + (current_window_size["width"] - inner_width)
        target_height = self.imageHeight + (current_window_size["height"] - inner_height)

        driver.set_window_rect(
            width=target_width,
            height=target_height)

    def get_screenshot(self):
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars");
        opts.add_argument('--force-device-scale-factor=1')
        driver = webdriver.Chrome(options=opts)
        self.set_viewport_size(driver)
        driver.get(self.htmlFile)
        sleep(1)
        driver.get_screenshot_as_file(self.currPath + '/calendar.png')
        driver.quit()

        self.logger.info('Screenshot captured and saved to file.')

        redimg = Image.open(self.currPath + '/calendar.png')  # get image)
        rpixels = redimg.load()  # create the pixel map
        blackimg = Image.open(self.currPath + '/calendar.png')  # get image)
        bpixels = blackimg.load()  # create the pixel map

        for i in range(redimg.size[0]):  # loop through every pixel in the image
            for j in range(redimg.size[1]): # since both bitmaps are identical, cycle only once and not both bitmaps
                if rpixels[i, j][0] <= rpixels[i, j][1] and rpixels[i, j][0] <= rpixels[i, j][2]:  # if is not red
                    rpixels[i, j] = (255, 255, 255)  # change it to white in the red image bitmap

                elif bpixels[i, j][0] > bpixels[i, j][1] and bpixels[i, j][0] > bpixels[i, j][2]:  # if is red
                    bpixels[i, j] = (255, 255, 255)  # change to white in the black image bitmap

        redimg = redimg.rotate(self.rotateAngle, expand=True)
        blackimg = blackimg.rotate(self.rotateAngle, expand=True)

        self.logger.info('Image colours processed. Extracted grayscale and red images.')
        return blackimg, redimg

    def get_day_in_cal(self, startDate, eventDate):
        delta = eventDate - startDate
        return delta.days

    def get_short_time(self, datetimeObj, is24hour=False):
        datetime_str = ''
        if is24hour:
            datetime_str = '{}:{:02d}'.format(datetimeObj.hour, datetimeObj.minute)
        else:
            if datetimeObj.minute > 0:
                datetime_str = '.{:02d}'.format(datetimeObj.minute)

            if datetimeObj.hour == 0:
                datetime_str = '12{}am'.format(datetime_str)
            elif datetimeObj.hour == 12:
                datetime_str = '12{}pm'.format(datetime_str)
            elif datetimeObj.hour > 12:
                datetime_str = '{}{}pm'.format(str(datetimeObj.hour % 12), datetime_str)
            else:
                datetime_str = '{}{}am'.format(str(datetimeObj.hour), datetime_str)
        return datetime_str

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
