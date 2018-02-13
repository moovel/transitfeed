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

"""
Given a stop_id, show all associated trips, routes, and service periods.
"""

import logging as log
import optparse
import sys
import transitfeed


log.basicConfig(format='%(asctime)s-15 %(message)s', level=log.DEBUG)


def show_stop_info(schedule, stop_id, date=None):
    stop = schedule.stops.get(stop_id)
    if not stop:
        print('stop_id [%s] not found in the gtfs data' % stop_id)
        return
    trips = stop.GetTrips(schedule)
    print('stop: %s' % stop)
    inactive_trips = 0
    trip_num = 0
    for trip in enumerate(trips):
        calendar = schedule.service_periods[trip.service_id]
        if not (date and calendar.IsActiveOn(date=date)):
            inactive_trips += 1
            continue
        trip_num += 1
        print('  trip [%s]: %s' % (trip_num, trip))
        print('    calendar: %s' % calendar.__dict__)
        route = schedule.routes[trip.route_id]
        print('    route: %s' % route)
    if inactive_trips:
        print('    [%s] inactive trips for this stop' % inactive_trips)


def main():
    parser = optparse.OptionParser(
        usage=("usage: %prog [options]\n"
               "Show related trips, routes, and calendar data for the given stop_id and gtfs file."),
        version="%prog " + transitfeed.__version__)
    parser.add_option("-d",
                      "--date",
                      dest="date",
                      type='str',
                      default=None,
                      help='A date in yyyymmdd format.  If provided, only show active trips on this date for the given stop-id.')
    parser.add_option("-g",
                      "--gtfs-file",
                      dest="gtfs_file",
                      type='str',
                      default=None)
    parser.add_option("-s",
                      "--stop-id",
                      dest="stop_id",
                      type="str",
                      default=None)
    (options, args) = parser.parse_args()
    if options.gtfs_file is None:
        print >>sys.stderr, "\n\nYou must provide -g|--gtfs-file\n\n"
        sys.exit(2)
    if options.stop_id is None:
        print >>sys.stderr, "\n\nYou must provide -s|--stop-id\n\n"
        sys.exit(2)

    loader = transitfeed.Loader(options.gtfs_file)
    log.info('loading gtfs file...')
    schedule = loader.Load()
    log.info('gtfs file loaded')

    show_stop_info(schedule, options.stop_id, options.date)


if __name__ == "__main__":
    main()
