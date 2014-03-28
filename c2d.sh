#!/bin/bash
for i in "$@"; do
a=`cat $i`
echo "${a//,/.}" | sed 's/ /\
'/g >> $i"_"
done

