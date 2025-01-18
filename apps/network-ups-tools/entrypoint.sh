nutCfgVolume="/etc/nut"
nutCfgFiles="ups.conf upsd.conf upsd.users"

echo "*** NUT upsd startup ***"

# more sanity: make sure our config files stick around
for cfgFile in ${nutCfgFiles}; do
	if [ -f ${nutCfgVolume}/${cfgFile} ]; then
		# bail out if users file is too permissive
		if [ "`stat -c '%a' ${nutCfgVolume}/${cfgFile}`" != "440" -o "`stat -c '%u' ${nutCfgVolume}/${cfgFile}`" != "`id -u nut`" ]; then
			printf "ERROR: '%s/%s' mode is too permissive.\n" ${nutCfgVolume} ${cfgFile}
			printf "\trecommended permissions: 0440\n"
			printf "\trecommended owner:"
			id nut
			printf "\n\ncurrent permissions:\n"
			stat ${nutCfgVolume}/upsd.users
			exit
		fi

		continue
      	fi

	printf "ERROR: config file '%s/%s' does not exist. You should create one, have a look at the README.\n" ${nutCfgVolume} ${cfgFile}
	exit
done

# initialize UPS driver
printf "Starting up the UPS drivers ...\n"
/usr/sbin/upsdrvctl start || { printf "ERROR on driver startup.\n"; exit; }

# run the ups daemon
printf "Starting up the UPS daemon ...\n"
exec /usr/sbin/upsd -D $* || { printf "ERROR on daemon startup.\n"; exit; }
