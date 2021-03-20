#!/bin/bash

MYNAME=$0
CURRENTDIR=$(dirname $(readlink -e $MYNAME))
# get the source code directory
SRCDIR=$(dirname $CURRENTDIR)

if [[ "$VIRTUAL_ENV" == "" ]] ; then
    if [[ ! -f "${SRCDIR}/python/bin/activate" ]] ; then
        virtualenv $SRCDIR/python --python=python3
    fi
    . $SRCDIR/python/bin/activate
    pip install -q -r $SRCDIR/requirements.txt
fi
