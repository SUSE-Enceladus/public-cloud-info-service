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


MYNAME=$0
CURRENTDIR=$(dirname $(readlink -e $MYNAME))
# get the source code directory
SRCDIR=$(dirname $CURRENTDIR)

USAGE="${0}: [--debug]"

DEBUG=
if [ $# -gt 1 ] ; then
  echo "$USAGE"
  exit 1
elif [ $# -eq 1 ] ; then
  if [[ "$1" = "--debug" ]] ; then
    DEBUG="--debug --warm-containers EAGER"
  else
    echo "$USAGE"
    exit 1
  fi
fi

sam local start-api $DEBUG --env-vars $SRCDIR/local_test_env.json
