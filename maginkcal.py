#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This project is designed for the WaveShare 12.48" eInk display. Modifications will be needed for other displays,
especially the display drivers and how the image is being rendered on the display. Also, this is the first project that
I posted on GitHub so please go easy on me. There are still many parts of the code (especially with timezone
conversions) that are not tested comprehensively, since my calendar/events are largely based on the timezone I'm in.
There will also be work needed to adjust the calendar rendering for different screen sizes, such as modifying of the
CSS stylesheets in the "render" folder.
"""
import datetime as dt
import time
import sys

from pytz import timezone
from gcal.gcal import GcalHelper
from render.render import RenderHelper
from power.power import PowerHelper
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import logging

def config():
    # Basic configuration settings (user replaceable)
    configFile = open('config.json')
    config = json.load(configFile)

    displayTZ = timezone(config['displayTZ']) # list of timezones - print(pytz.all_timezones)
    thresholdHours = config['thresholdHours']  # considers events updated within last 12 hours as recently updated
    maxEventsPerDay = config['maxEventsPerDay']  # limits number of events to display (remainder displayed as '+X more')
    isDisplayToScreen = config['isDisplayToScreen']  # set to true when debugging rendering without displaying to screen
    isShutdownOnComplete = config['isShutdownOnComplete']  # set to true to conserve power, false if in debugging mode
    batteryDisplayMode = config['batteryDisplayMode']  # 0: do not show / 1: always show / 2: show when battery is low
    weekStartDay = config['weekStartDay']  # Monday = 0, Sunday = 6
    dayOfWeekText = config['dayOfWeekText'] # Monday as first item in list
    screenWidth = config['screenWidth']  # Width of E-Ink display. Default is landscape. Need to rotate image to fit.
    screenHeight = config['screenHeight']  # Height of E-Ink display. Default is landscape. Need to rotate image to fit.
    imageWidth = config['imageWidth']  # Width of image to be generated for display.
    imageHeight = config['imageHeight'] # Height of image to be generated for display.
    rotateAngle = config['rotateAngle']  # If image is rendered in portrait orientation, angle to rotate to fit screen
    calendars = config['calendars']  # Google calendar ids
    is24hour = config['is24h']  # set 24 hour time

    return displayTZ, thresholdHours, maxEventsPerDay, isDisplayToScreen, \
        isShutdownOnComplete, batteryDisplayMode, weekStartDay, dayOfWeekText, \
        screenWidth, screenHeight, imageWidth, imageHeight, rotateAngle, \
        calendars, is24hour

def displayCalendar(logger, displayService, renderService, gcalService):
    try:
        # Establish current date and time information
        # Note: For Python datetime.weekday() - Monday = 0, Sunday = 6
        # For this implementation, each week starts on a Sunday and the calendar begins on the nearest elapsed Sunday
        # The calendar will also display 5 weeks of events to cover the upcoming month, ending on a Saturday

        displayTZ, thresholdHours, maxEventsPerDay, isDisplayToScreen, \
        isShutdownOnComplete, batteryDisplayMode, weekStartDay, dayOfWeekText, \
        screenWidth, screenHeight, imageWidth, imageHeight, rotateAngle, \
        calendars, is24hour = config()

        logger.info("Calendar display start!")

        powerService = PowerHelper()
        powerService.sync_time()
        currBatteryLevel = powerService.get_battery()
        logger.info('Battery level at start: {:.3f}'.format(currBatteryLevel))

        currDatetime = dt.datetime.now(displayTZ)
        logger.info("Time synchronised to {}".format(currDatetime))
        currDate = currDatetime.date()
        calStartDate = currDate - dt.timedelta(days=((currDate.weekday() + (7 - weekStartDay)) % 7))
        # Populate dictionary with information to be rendered on e-ink display
        calDict = {'events': gcalService.get_events(), 'calStartDate': calStartDate, 'today': currDate, 'lastRefresh': currDatetime,
                   'batteryLevel': currBatteryLevel, 'batteryDisplayMode': batteryDisplayMode,
                   'dayOfWeekText': dayOfWeekText, 'weekStartDay': weekStartDay, 'maxEventsPerDay': maxEventsPerDay,
                   'is24hour': is24hour}

        calBlackImage, calRedImage = renderService.process_inputs(calDict)

        if isDisplayToScreen:
            if currDate.weekday() == weekStartDay:
                # calibrate display once a week to prevent ghosting
                displayService.calibrate(cycles=0)  # to calibrate in production
            displayService.update(calBlackImage, calRedImage)

        currBatteryLevel = powerService.get_battery()
        logger.info('Battery level at end: {:.3f}'.format(currBatteryLevel))

    except Exception as e:
        logger.error(e)

    logger.info("Completed calendar update")
    return

def syncCalendar(logger, gcalService):
    displayTZ, thresholdHours, maxEventsPerDay, isDisplayToScreen, \
    isShutdownOnComplete, batteryDisplayMode, weekStartDay, dayOfWeekText, \
    screenWidth, screenHeight, imageWidth, imageHeight, rotateAngle, \
    calendars, is24hour = config()
    global eventList

    logger.info("Calendar sync start!")

    currDatetime = dt.datetime.now(displayTZ)
    logger.info("Time synchronised to {}".format(currDatetime))
    currDate = currDatetime.date()
    calStartDate = currDate - dt.timedelta(days=((currDate.weekday() + (7 - weekStartDay)) % 7))
    calEndDate = calStartDate + dt.timedelta(days=(5 * 7 - 1))
    calStartDatetime = displayTZ.localize(dt.datetime.combine(calStartDate, dt.datetime.min.time()))
    calEndDatetime = displayTZ.localize(dt.datetime.combine(calEndDate, dt.datetime.max.time()))

    # Using Google Calendar to retrieve all events within start and end date (inclusive)
    start = dt.datetime.now(displayTZ)

    eventList = gcalService.retrieve_events(calendars, calStartDatetime, calEndDatetime, displayTZ, thresholdHours)
    logger.info("Calendar events retrieved in " + str(dt.datetime.now(displayTZ) - start))

    return

if __name__ == "__main__":
    # Create and configure logger
    logging.basicConfig(filename="logfile.log", format='%(asctime)s %(levelname)s - %(message)s', filemode='a')
    logger = logging.getLogger('maginkcal')
    logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
    logger.setLevel(logging.INFO)
    logger.info("Starting daily calendar update")

    displayTZ, thresholdHours, maxEventsPerDay, isDisplayToScreen, \
    isShutdownOnComplete, batteryDisplayMode, weekStartDay, dayOfWeekText, \
    screenWidth, screenHeight, imageWidth, imageHeight, rotateAngle, \
    calendars, is24hour = config()

    if isDisplayToScreen:
    # initialize display
        from display.display import DisplayHelper
        displayService = DisplayHelper(screenWidth, screenHeight)
    
    sched = BlockingScheduler()
    renderService = RenderHelper(imageWidth, imageHeight, rotateAngle)
    gcalService = GcalHelper()

    syncCalendar(logger, gcalService)
    displayCalendar(logger, displayService, renderService, gcalService)

    sched.add_job(lambda: displayCalendar(logger, displayService, renderService, gcalService),
        CronTrigger.from_crontab(
            "4,9,14,19,24,29,34,39,44,49,54,59 * * * *"
        ),
        id='display'
    )
    sched.add_job(lambda: syncCalendar(logger, gcalService),
        CronTrigger.from_crontab(
            "2,7,12,17,22,27,32,37,42,47,52,57 * * * *"
        ),
        id="event_sync"
    )

    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        displayService.epd.clear()
        displayService.sleep()
