#!/bin/bash

#activar GPIO 13 y 18 como salidas de audio (requiere expansión hardware)

gpio -g mode 18 ALT5
gpio -g mode 13 ALT0

cd /home/pi/cliente
sudo python cliente.py
