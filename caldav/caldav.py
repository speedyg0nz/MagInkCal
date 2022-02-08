#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is where we retrieve events from a caldav calendar.
This requires a valid credentials.json file in this same directory.
"""

from __future__ import print_function
import datetime as dt
import os.path
import pathlib
import logging
import caldav

class CaldavHelper:

    def __init__(self):
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())

        if not os.path.exists(self.currPath + '/credentials.json'):
            raise Exception("No caldav 'credentials.json' file found.")
        try:
            credsFile = open(self.currPath + '/credentials.json')
            creds = json.load(credsFile)
        except:
            raise Exception("Could not parse caldav 'credentials.json' file.")
        
        client = caldav.DAVClient(url=creds["url"], username=creds["username"], password=creds["password"])
        self.principal = client.principal()


    def list_calendars(self):
        # helps to retrieve ID for calendars within the account
        # calendar IDs added to config.json will then be queried for retrieval of events
        self.logger.info('Getting list of calendars')
        calendars_result = self.principal.calendars()
        if not calendars_result:
            self.logger.info('No calendars found.')
        for calendar in calendars_result:
            self.logger.info("%s\t%s" % (calendar.name, calendar.url))

    def is_recent_updated(self, updatedTime, thresholdHours):
        # consider events updated within the past X hours as recently updated
        utcnow = dt.datetime.now(dt.timezone.utc)
        diff = (utcnow - updatedTime).total_seconds() / 3600  # get difference in hours
        return diff < thresholdHours

    def adjust_end_time(self, endTime):
        # check if end time is at 00:00 of next day, if so set to max time for day before
        if endTime.hour == 0 and endTime.minute == 0 and endTime.second == 0:
            newEndtime = dt.datetime.combine(endTime.date() - dt.timedelta(days=1), dt.datetime.max.time())
            return newEndtime
        else:
            return endTime

    def is_multiday(self, start, end):
        # check if event stretches across multiple days
        if type(start) is dt.datetime:
            return start.date() != end.date()
        else:
            return start != end

    def normalize_datetime(self, dateobj, localTZ):
        # Always returns datetime object -- whether date or datetime given
        if type(dateobj) is dt.date:
            dateobj = dt.datetime.combine(dateobj, dt.datetime.min.time())
        if dateobj.tzinfo is None:
            dateobj = localTZ.localize(dateobj)
        return dateobj


    def retrieve_events(self, calendars, startDatetime, endDatetime, localTZ, thresholdHours):
        eventList = []

        minTimeStr = startDatetime.isoformat()
        maxTimeStr = endDatetime.isoformat()

        self.logger.info('Retrieving events between ' + minTimeStr + ' and ' + maxTimeStr + '...')
        events_result = []
        for cal in self.principal.calendars():
            if cal.name in calendars:
                search_results = cal.date_search(
                    start=startDatetime,
                    end=endDatetime,
                    expand=True
                )
                for evt in search_results:
                    events_result.append(evt.vobject_instance.vevent)

        if not events_result:
            self.logger.info('No upcoming events found.')
        for event in events_result:
            # extracting and converting events data into a new list
            newEvent = {}
            newEvent['summary'] = event.summary.value
            startTime = event.dtstart.value
            endTime = event.dtend.value

            # if dt.date, full-day event. if dt.datetime, time-boundaries are set
            newEvent['startDatetime'] = self.normalize_datetime(startTime, localTZ)
            newEvent['endDatetime'] = self.adjust_end_time(self.normalize_datetime(endTime, localTZ))
            newEvent['allday'] = type(startTime) is dt.date

            # If event hasn't been updated, use creation time
            if hasattr(event, "last_modified"):
                newEvent['updatedDatetime'] = event.last_modified.value
            elif hasattr(event, "created"):
                newEvent['updatedDatetime'] = event.created.value
            if 'updatedDatetime' in newEvent:
                newEvent['isUpdated'] = self.is_recent_updated(newEvent['updatedDatetime'], thresholdHours)
            
            # Deduce other properties
            newEvent['isMultiday'] = self.is_multiday(newEvent['startDatetime'], newEvent['endDatetime'])
            eventList.append(newEvent)

        # We need to sort eventList because the event will be sorted in "calendar order" instead of hours order
        eventList = sorted(eventList, key=lambda k: k['startDatetime'])
        return eventList
