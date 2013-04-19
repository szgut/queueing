for((;;)) do
	echo "reset"
	echo "set xrange ["1":"63"]"
	echo "set yrange ["1":"63"]"
	echo "set zrange ["1":"63"]"
	echo "splot '"$1".metals' using 1:2:3"
	sleep 5;
done
