#!/bin/bash

VENV_NAME=test_venv
MYNAME=$0
CURRENTDIR=$(dirname $(readlink -e $MYNAME))
# get the source code directory
SRCDIR=$(dirname $CURRENTDIR)

if [[ "$VIRTUAL_ENV" == "" ]] ; then
    if [[ ! -f "${SRCDIR}/${VENV_NAME}/bin/activate" ]] ; then
        virtualenv $SRCDIR/$VENV_NAME --python=python3
    fi
    . $SRCDIR/$VENV_NAME/bin/activate
    pip install -q -r $SRCDIR/test-requirements.txt
fi
