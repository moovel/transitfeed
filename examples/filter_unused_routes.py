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


"""Filter the unused routes out of a transit feed file."""

from datetime import date

import optparse
import sys
import transitfeed

DATE_CUTOFF_MIN = 20170101  # 1/1/2017; date sanity check
DATE_CUTOFF_MAX = 20220101  # 1/1/2022; date sanity check


def remove_unused_routes(schedule, rm_if_end_date_before):
    print "Removing unused routes..."
    removed_routes = 0
    idx = 1
    total_routes = len(schedule.routes)
    for route_id, route in schedule.routes.items():
        print("Processing route num [%s] of [%s], route_id=[%s] route_short_name=[%s] route_long_name=[%s] num trips = [%s]" % (idx, total_routes, route.route_id, route.route_short_name, route.route_long_name, len(route.trips)))
        idx += 1
        # if this route doesn't have any trips with an end_date after the cutoff date, then remove it
        rm_this_route = True
        date_ranges = set()
        services = set()
        for trip in route.trips:
            service = trip._schedule.service_periods[trip.service_id]
            services.add(service)
            end_date = date(year=int(service.end_date[0:4]),
                            month=int(service.end_date[4:6]),
                            day=int(service.end_date[6:8]))
            date_ranges.add('%s-%s' % service.GetDateRange())
            if end_date >= rm_if_end_date_before:
                rm_this_route = False

        if rm_this_route:
            removed_routes += 1
            del schedule.routes[route_id]
            print "Removing route_id=[%s] route_short_name=[%s] route_long_name=[%s] date_ranges=%s" % (route_id, route.route_short_name, route.route_long_name, date_ranges)
        elif len(services) > 1:
            print "Multiple services ([%s]) for route_id=[%s]" % (len(services), route_id)
    print("Removed [%d] route(s) of [%s] total routes, kept [%s] routes" % (removed_routes, total_routes, total_routes - removed_routes))


def remove_unused_stops(schedule):
    num_removed = 0
    total_stops = len(schedule.stops)
    print("Removing unused stops. Total number of stops to check = [%s]" % total_stops)
    for stop_id, stop in schedule.stops.items():
        if not stop.GetTrips(schedule):
            num_removed += 1
            del schedule.stops[stop_id]
            print("Removed stop_id=[%s] name=[%s])" % (stop_id, stop.stop_name))
    print("Removed [%s] of [%s] stops, leaving [%s] stops" % (num_removed, total_stops, total_stops - num_removed))



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
    parser.add_option("-l", "--list_removed", dest="list_removed",
                      default=False,
                      action="store_true",
                      help="Print removed routes to stdout")
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

    remove_unused_routes(schedule, rm_if_end_date_before)
    remove_unused_stops(schedule)

    schedule.WriteGoogleTransitFeed(output_path)


if __name__ == "__main__":
    main()
