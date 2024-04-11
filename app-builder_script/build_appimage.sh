#!/bin/bash

# Default architecture
ARCH=x86_64

# Parse command line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --arch=*) ARCH="${1#*=}"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Delete AppDir if it exists
if [ -d "AppDir" ]; then
    echo "Removing existing AppDir..."
    rm -rf AppDir
fi

# Recreate AppDir
mkdir AppDir
mkdir AppDir/usr
mkdir AppDir/usr/src

# Copy AppRun and AppInfo.xml from resources
cp resources/AppRun resources/AppInfo.xml AppDir/

# Verify that resources directory exists
if [ ! -d "resources" ]; then
    echo "The 'resources' directory does not exist."
    exit 1
fi

# Copy files and directory
cp resources/icon.png resources/appopssat.desktop AppDir/
cp resources/appopssat.desktop ./
cp -r resources/usr AppDir/
cp -r gr-scripts/* AppDir/usr/src

echo "Files and directories have been successfully copied to AppDir."

echo "Download linuxdeploy-$ARCH.AppImage ..."
wget -c -P ./resources/ "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-$ARCH.AppImage"
echo "... Done"

export CONDA_CHANNELS=ryanvolz
export CONDA_PACKAGES="gnuradio-gpredict-doppler=0.0.0.20231030.dev+g7114d423e unix_pyh9f2d41d_0;gnuradio=3.10.9.2;gnuradio-satellites=5.5.0;pyqt=5.15.9;qt=5.15.8;pyzmq=25.1.2;crccheck=1.3.0;gnuradio-osmosdr=0.2.4"
export PIP_REQUIREMENTS="numpy==1.26.3 requests==2.31.0"
export QT_SELECT=5


chmod +x ./resources/linuxdeploy-$ARCH.AppImage
chmod +x ./resources/linuxdeploy-plugin-conda.sh
ARCH=$ARCH ./resources/linuxdeploy-$ARCH.AppImage --appdir AppDir -i AppDir/usr/conda/data/Mod/Start/StartPage/icon.png -d appopssat.desktop --plugin=conda --output appimage

rm ./appopssat.desktop
chmod +x ./opssat_uhf-$ARCH.AppImage