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

RM_IF_END_DATE_BEFORE = date(year=2017, month=6, day=12)


def main():
    parser = optparse.OptionParser(
        usage="usage: %prog [options] input_feed output_feed",
        version="%prog "+transitfeed.__version__)
    parser.add_option("-l", "--list_removed", dest="list_removed",
                      default=False,
                      action="store_true",
                      help="Print removed routes to stdout")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        print >>sys.stderr, parser.format_help()
        print >>sys.stderr, "\n\nYou must provide input_feed and output_feed\n\n"
        sys.exit(2)
    input_path = args[0]
    output_path = args[1]

    loader = transitfeed.Loader(input_path)
    schedule = loader.Load()

    print "Removing unused routes..."
    removed = 0
    idx = 1
    for route_id, route in schedule.routes.items():
        print("Processing route num [%s], route_id=[%s] route_short_name=[%s] route_long_name=[%s] num trips = [%s]" % (idx, route.route_id, route.route_short_name, route.route_long_name, len(route.trips)))
        if str(route.route_short_name) == '208':
            # import pdb
            # pdb.set_trace()
            pass
        idx += 1
        # if this route doesn't have any trips with an end_date after 20170612, then remove it
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
            if end_date >= RM_IF_END_DATE_BEFORE:
                rm_this_route = False

        if rm_this_route:
            removed += 1
            del schedule.routes[route_id]
            if options.list_removed:
                print "Removing route_id=[%s] route_short_name=[%s] route_long_name=[%s]" % (route_id, route.route_short_name, route.route_long_name)
                print "date_ranges: %s" % date_ranges
        elif len(date_ranges) > 1:
            print "Multiple services for this trip: %s" % date_ranges
        if removed == 0:
            print "There were no unused routes to remove."
        else:
            print "Removed [%d] routes(s)" % removed

    schedule.WriteGoogleTransitFeed(output_path)


if __name__ == "__main__":
    main()
