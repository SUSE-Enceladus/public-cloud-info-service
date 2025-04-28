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


CurrentDir=$(dirname $(readlink -e $0))
ProjectRootDir=$(dirname $CurrentDir)

export PYTHONPATH=${ProjectRootDir}:${PYTHONPATH:+:${PYTHONPATH}}

if [[ "$VIRTUAL_ENV" == "" ]] ; then
  echo
  echo "ERROR: python virtualenv not detected. Please run $CurrentDir/create_dev_venv.sh to create and activate the python venv first."
  echo
  exit 1
fi

python3.11 ${ProjectRootDir}/pint_server/data_update.py $@
