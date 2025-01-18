#!/bin/sh

echo "*** NUT upsd startup ***"

if [ -f /config/ups.conf ]; then
  # Initialize UPS driver if ups.conf exists
  printf "Starting up the UPS drivers ...\n"
  /usr/sbin/upsdrvctl -u root start || { printf "ERROR on driver startup.\n"; exit 1; }
else
  printf "Skipping UPS driver startup. No ups.conf found.\n"
fi

# Run the UPS daemon
printf "Starting up the UPS daemon ...\n"
exec /usr/sbin/upsd -u root -D "$@" || { printf "ERROR on daemon startup.\n"; exit 1; }
