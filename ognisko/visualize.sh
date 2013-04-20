#!/bin/bash

echo "set terminal x11"
for((;;)) do
	echo "set xrange ["1":"$2"]"
	echo "set yrange ["1":"$2"]"
	echo "set zrange ["1":"150"]"
	echo -n "plot '"$1".lands' using 1:2 with points, "
	echo -n "'"$1".beetles' using 1:2 with points pointtype 3, "
	echo "'"$1".target' using 1:2 with points pointtype 3 pointsize 4"
	sleep 1;
done
