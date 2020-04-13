#!/bin/bash

echo "setting TV volume to $1"

#let "vol = 100 - $1"
echo $1 > /dev/ttyUSB0

#echo "set TV attenuation to $vol."
