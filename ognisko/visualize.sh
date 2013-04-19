#!/bin/bash

echo "set terminal x11"
for((;;)) do
	echo "set xrange ["1":"300"]"
	echo "set yrange ["1":"300"]"
	echo -n "plot '"$1".lands' using 1:2 with points, "
	echo "'"$1".beetles' using 1:2 with points pointtype 3"
	sleep 5;
done