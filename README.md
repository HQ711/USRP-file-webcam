# USRP-file-webcam
Enviorment: Ubuntu 18.04
            Python2.7
            Gnuradio3.7

Transmitter:
e.g. For webcam use following command

     python transmitter.py -a addr=192.168.10.2 --tx-freq=2.45e9 -r 500e3 -m gmsk --live
Args invoved:

     -a                 USRP address
     
     -m                 Modulation type(Default GMSK)
     
     --tx-freq          transmitter frequency
     
     -r                 bit rate
     
     -s                 Packet Size(range 0-4096)
     
     -M                 megabytes to transmit
     
     --discontinuous    enable burst transmission
     
     --from-file        File address
     
     --live             enable live play(default store the data)
     
     --pyrdown          pyrdown the video
     
Receiver:
e.g. For webcam use following command

     python receiver.py -a addr=192.168.20.2 --rx-freq=2.45e9 -m gmsk -r 500e3 --live
Args invoved:
     -a                 USRP address
     -m                 Modulation type(Default GMSK)
     --rx-freq          receiver frequency
     -r                 bit rate
     --to-file          File address
     --live             enable live play(default store the data)

udp_client:
python udp_client.py
to show the live video
