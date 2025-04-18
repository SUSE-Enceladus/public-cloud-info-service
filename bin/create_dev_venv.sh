#!/bin/bash
# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com


VENV_NAME=dev_venv
MYNAME=$0
CURRENTDIR=$(dirname $(readlink -e $MYNAME))
# get the source code directory
SRCDIR=$(dirname $CURRENTDIR)

if [[ "$VIRTUAL_ENV" == "" ]] ; then
    if [[ ! -f "${SRCDIR}/${VENV_NAME}/bin/activate" ]] ; then
        virtualenv $SRCDIR/$VENV_NAME --python=python3.11
    fi
    . $SRCDIR/$VENV_NAME/bin/activate
    pip install -q --upgrade pip wheel setuptools
    pip install -q -r $SRCDIR/requirements.txt
fi
