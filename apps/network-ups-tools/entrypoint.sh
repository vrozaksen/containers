#!/bin/sh

echo "*** NUT upsd startup ***"

if [ -f /config/ups.conf ]; then
  # Check if ups.conf contains "driver = none" or "driver=none"
  if grep -qE '^\s*driver\s*=\s*none' /config/ups.conf; then
    printf "Skipping UPS driver startup. 'driver = none' found in ups.conf.\n"
  else
    # Initialize UPS driver
    printf "Starting up the UPS drivers ...\n"
    /usr/sbin/upsdrvctl -u root start || { printf "ERROR on driver startup.\n"; exit 1; }
  fi
else
  printf "Skipping UPS driver startup. No ups.conf found.\n"
fi

# Run the UPS daemon
printf "Starting up the UPS daemon ...\n"
exec /usr/sbin/upsd -u root -D "$@" || { printf "ERROR on daemon startup.\n"; exit 1; }
