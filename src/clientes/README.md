video-image
===========

Este programa es solo para tomar una foto desde una cámara digital 
usando el puerto serial del beaglebone black.

Se basa en el demo de Adafruit y será actualizado en el futuro

El programa getimage toma una imagen en 320x240.

Para configurar los puertos seriales del BBB se require:

http://www.armhf.com/index.php/beaglebone-black-serial-uart-device-tree-overlays-for-ubuntu-and-debian-wheezy-tty01-tty02-tty04-tty05-dtbo-files/

para poder realizar los comandos de abajo, se deben cambiar los atributos de slots
sudo chmod 666 /sys/devices/bone_capemgr*/slots

Copiar los archivos .dtbo al directorio /lib/firmware y aplicar el siguiente comando después de copiarlo. sudo echo ttyO1_armhf.com > /sys/devices/bone_capemgr*/slots

    ttyO1_armhf.com-00A0.dtbo
    ttyO2_armhf.com-00A0.dtbo
    ttyO4_armhf.com-00A0.dtbo
    ttyO5_armhf.com-00A0.dtbo

Estos archivos se encuentran en el directorio /sistema

Nota 1: ttyO3 no tiene pin RX (Está ligado al chip HDMI TDA19988)
Nota 2: ttyO5 comparte pins con el HDMI – ambos no pueden estar activos al mismo tiempo
nota 3: ttyO0 está disponible en J1 y no require de activación
