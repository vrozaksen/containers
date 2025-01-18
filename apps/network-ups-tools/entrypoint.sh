#!/usr/bin/env bash
set -e

echo "*** NUT upsd startup ***"

# initialize UPS driver
printf "Starting up the UPS drivers ...\n"
/usr/sbin/upsdrvctl -u root start || { printf "ERROR on driver startup.\n"; exit; }

# run the ups daemon
printf "Starting up the UPS daemon ...\n"
exec /usr/sbin/upsd -u root -D $* || { printf "ERROR on daemon startup.\n"; exit; }
