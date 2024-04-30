# gr-opssat

Original authors: Fischer Benjamin (benjamin.fischer@arcticspacetech.com), Tom Mladenov (tom.mladenov@esa.int)

This repository contains documentation, and applications for receiving, demodulating, and decoding the UHF signal transmitted by the ESA OPS-SAT mission. It also contains a full graphical application for viewing and parsing the beacon frames transmitted by OPS-SAT.

https://opssat1.esoc.esa.int/
https://opssat1.esoc.esa.int/projects/amateur-radio-information-bulletin

https://www.esa.int/Our_Activities/Operations/OPS-SAT

## Overview

### UHF specifications
Can be found in docs/os-uhf-specs.pdf

### Applications

Authors: Guilhem Honore, Maxence Beuselinck, Tim Oerther

The project has been taken over to be wrapped as an AppImage and the dependencies updated. You can find the releases for x86_64 and aarch64.
To build it yourself, you can set as executable and run the script [build_appimage.sh](./app-builder_script/build_appimage.sh).
The goal of the AppImage is to have a working out-of-the-box project for all amateur radio operator.

## Getting started
There are two ways to use the application to send us data. The appimage available for linux in x86_64 and aarch64 architecture is a system designed to work out-of-the-box. The source code is also available in the gnuradio-companion scripts, enabling you to set up other SDRs and run it on other systems. However, this requires more work in terms of installing dependencies.
### AppImage
Please download the appropriate [AppImage](https://github.com/esa/gr-opssat/releases), run the AppImage with
```
chmod +x opssat_uhf-$ARCH.AppImage #set the AppImage as exectuable
./opssat_uhf-$ARCH.AppImage
```

#### Operational usage with live reception
For operational usage, please look at the [UHF campain guide - AppImage](docs/UHF_Campain_GUIDE-AppImage.md)

### GNU Radio companion scripts
Please download the source from the folder `./app-grc_script`

#### Operational usage with live reception
For operational usage, please look at the [UHF campain guide - GRC Scripts](docs/UHF_Campain_GUIDE-Scripts.md)

## Desktop interface

It receives the RS decoded CSP packet + 4 byte CRC32-C over a ZMQ socket on localhost port 38211 to which it is subscribed.
You should now see beacon frames being parsed and displayed:

![screenshot](images/opssat_desktop.png)

The raw packet history shows the received packets, CRC check status and CSP header information.

This application writes to 3 logfiles in a temporary folder located in `/tmp/` or your linux machine:
* One log contains the raw received hex data (raw.log)
* The second log contains the parsed beacon telemetry (parsed_beacon.log)
* The third log contains timestamped events generated by the application (gui_event.log)



