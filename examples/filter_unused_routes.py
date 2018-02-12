#!/usr/bin/python2.5

# Copyright (C) 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Filter the unused services, routes, trips, and stops out of a gtfs (transit feed) file."""

from datetime import date

import optparse
import sys
import transitfeed

DATE_CUTOFF_MIN = 20170101  # 1/1/2017; date sanity check
DATE_CUTOFF_MAX = 20220101  # 1/1/2022; date sanity check


def get_service_ids_to_remove(schedule, rm_if_end_date_before):
    # A service_period can be removed if it's end_date < rm_if_end_date_before
    service_ids_to_remove = set()
    for service in schedule.service_periods.values():
        end_date = date(year=int(service.end_date[0:4]),
                        month=int(service.end_date[4:6]),
                        day=int(service.end_date[6:8]))
        if end_date < rm_if_end_date_before:
            print('Removing service period id=[%s] start_date=[%s] end_date=[%s]' % (service.service_id, service.start_date, service.end_date))
            service_ids_to_remove.add(service.service_id)
    print('Service periods: removing [%s] of [%s], remaining=[%s]'
          % (len(service_ids_to_remove),
             len(schedule.service_periods),
             len(schedule.service_periods) - len(service_ids_to_remove)))
    return service_ids_to_remove


def get_trip_ids_to_remove(schedule, service_ids_to_remove):
    # A trip can be removed if it's service_period is in service_ids_to_remove
    trip_ids_to_remove = set()
    for trip in schedule.trips.values():
        if trip.service_id in service_ids_to_remove:
            trip_ids_to_remove.add(trip.trip_id)
    print('Trips: removing [%s] of [%s], remaining=[%s]'
          % (len(trip_ids_to_remove),
             len(schedule.trips),
             len(schedule.trips) - len(trip_ids_to_remove)))
    return trip_ids_to_remove


def get_route_ids_to_remove(schedule, trip_ids_to_remove):
    # A route can be removed if all it's trips are in trip_ids_to_remove
    route_ids_to_remove = set()
    for route in schedule.routes.values():
        rm_route = True
        for trip in route.trips:
            if trip.trip_id not in trip_ids_to_remove:
                rm_route = False
                break
        if rm_route:
            route_ids_to_remove.add(route.route_id)
            print("Removing route_id=[%s] route_short_name=[%s] route_long_name=[%s]" % (route.route_id, route.route_short_name, route.route_long_name))
    print('Routes: removing [%s] of [%s], remaining=[%s]'
          % (len(route_ids_to_remove),
             len(schedule.routes),
             len(schedule.routes) - len(route_ids_to_remove)))
    return route_ids_to_remove


def get_stop_ids_to_remove(schedule, trip_ids_to_remove):
    # A stop can be removed if all it's trips are in trip_ids_to_remove
    stop_ids_to_remove = set()
    for stop in schedule.stops.values():
        rm_stop = True
        for trip in stop.GetTrips(schedule):
            if trip.trip_id not in trip_ids_to_remove:
                rm_stop = False
                break
        if rm_stop:
            stop_ids_to_remove.add(stop.stop_id)
            print("Removed stop_id=[%s] name=[%s])" % (stop.stop_id, stop.stop_name))
    print('Stops: removing [%s] of [%s], remaining=[%s]'
          % (len(stop_ids_to_remove),
             len(schedule.stops),
             len(schedule.stops) - len(stop_ids_to_remove)))
    return stop_ids_to_remove


def main():
    parser = optparse.OptionParser(
        usage="usage: %prog [options] input_feed output_feed",
        version="%prog "+transitfeed.__version__)
    parser.add_option("-d",
                      "--date-cutoff",
                      dest="date_cutoff",
                      type="int",
                      default=0,
                      help="Remove all routes before (less than) this date.  Format: yyyymmdd")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        print >>sys.stderr, parser.format_help()
        print >>sys.stderr, "\n\nYou must provide input_feed and output_feed\n\n"
        sys.exit(2)
    if options.date_cutoff == 0:
        print >>sys.stderr, "\n\nYou must provide -d|--date-cutoff\n\n"
        sys.exit(2)
    if (options.date_cutoff < DATE_CUTOFF_MIN) or (options.date_cutoff > DATE_CUTOFF_MAX):
        print >>sys.stderr, "-d|--date-cutoff must be an int in the format yyyymmdd and %s < yyyymmdd < %s" % (DATE_CUTOFF_MIN, DATE_CUTOFF_MAX)
        sys.exit(2)
    date_str = str(options.date_cutoff)
    rm_if_end_date_before = date(year=int(date_str[:4]),
                                 month=int(date_str[4:6]),
                                 day=int(date_str[6:8]))
    input_path = args[0]
    output_path = args[1]

    loader = transitfeed.Loader(input_path)
    schedule = loader.Load()
    print('Finished reading gtfs file')

    service_ids_to_rm = get_service_ids_to_remove(schedule, rm_if_end_date_before)
    trip_ids_to_rm = get_trip_ids_to_remove(schedule, service_ids_to_rm)
    route_ids_to_rm = get_route_ids_to_remove(schedule, trip_ids_to_rm)
    stop_ids_to_rm = get_stop_ids_to_remove(schedule, trip_ids_to_rm)

    for stop_id in stop_ids_to_rm:
        del schedule.stops[stop_id]
    for trip_id in trip_ids_to_rm:
        del schedule.trips[trip_id]
    for route_id in route_ids_to_rm:
        del schedule.routes[route_id]
    for service_id in service_ids_to_rm:
        del schedule.service_periods[service_id]

    print("Writing new gtfs file...")
    schedule.WriteGoogleTransitFeed(output_path)


if __name__ == "__main__":
    main()
