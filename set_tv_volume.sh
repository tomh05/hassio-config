#!/bin/bash

echo "setting TV volume to $1"

echo $1 > /dev/ttyUSB0

echo "set TV volume to $1."
