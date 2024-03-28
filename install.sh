#!/bin/bash
######### INSTALLER FOR THIS PACKAGE INTO PYTHON PATH

TARGETDIR=~/micromamba/envs/ms-atr/lib/python3.8/

SOURCEDIR=$( echo $PWD )
MODULE_NAME=$( basename $PWD )
echo "Installing module: ${MODULE_NAME}"
echo "             from: ${SOURCEDIR}"
echo "               to: ${TARGETDIR}" && echo

mkdir -p $TARGETDIR/$MODULE_NAME
cp -r ./* $TARGETDIR/$MODULE_NAME
