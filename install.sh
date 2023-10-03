#!/bin/bash
######### INSTALLER FOR THIS PACKAGE INTO PYTHON PATH

TARGETDIR=~/.local/lib/python3.8/site-packages

SOURCEDIR=$( echo $PWD )
MODULE_NAME=$( basename $PWD )
echo "Installing module: ${MODULE_NAME}"
echo "             from: ${SOURCEDIR}"
echo "               to: ${TARGETDIR}" && echo

mkdir -p $TARGETDIR/$MODULE_NAME
cp -r ./* $TARGETDIR/$MODULE_NAME