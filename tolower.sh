#!/bin/sh
# Converts file names to lower case.
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Last modified: 2016-03-19 10:38:03 +0100
#
# To the extent possible under law, Roland Smith has waived all copyright and
# related or neighboring rights to 'tolower'. This work is published from the
# Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

set -eu

if [ $# -eq 0 ]; then
    echo "Usage: tolower filenames"
fi

for f in $*; do
    n=$(echo $f|tr [:upper:] [:lower:])
    #echo "moving $f to $n"
    mv $f $n
done
