#!/bin/bash

echo "setting TV volume to $1"

let "vol = 100 - $1"
echo $vol > /dev/ttyUSB0

echo "set TV attenuation to $vol."
