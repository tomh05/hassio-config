#!/bin/bash

echo "setting TV volume to $1"

#let "vol = 100 - $1"
stty -F /dev/ttyUSB0 -echo
echo $1 > /dev/ttyUSB0

#echo "set TV attenuation to $vol."
