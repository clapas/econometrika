#!/bin/bash
sed -i -e 's/"\(-\?[[:digit:]]\+\),\([[:digit:]]\+\)"/\1.\2/g' $1
sed -i -e 's/\(\([^,]\+,\)\{3\}\)[^,]\+,/\1/g' $1
sed -i '1 s/^.*$/date,close,open,high,low,volume/' $1
sed -i 's/ene/01/gi; s/feb/02/gi; s/mar/03/gi; s/abr/04/gi; s/may/05/gi; s/jun/06/gi; s/jul/07/gi; s/ago/08/gi; s/sep/09/gi; s/oct/10/gi; s/nov/11/gi; s/dic/12/gi' $1 
sed -i 's/\([[:digit:]]\{2\}\)-\([[:digit:]]\{2\}\)-\([[:digit:]]\{4\}\)/\3-\2-\1/g' $1
