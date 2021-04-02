#!/bin/bash

MYNAME=$0
CURRENTDIR=$(dirname $(readlink -e $MYNAME))
# get the source code directory
SRCDIR=$(dirname $CURRENTDIR)

# check to see if we are running inside the python virtual environment
if [[ "$VIRTUAL_ENV" == "" ]] ; then
  echo
  echo "ERROR: python virtualenv not detected. Please run $CURRENTDIR/create_venv.sh to create and activate the python venv first."
  echo
  exit 1
fi

export POSTGRES_USER=snotty
export POSTGRES_PASSWORD=MasterSlobs
export POSTGRES_DB=postgres
export POSTGRES_HOST=127.0.0.1
# NOTE(gyee): see https://www.postgresql.org/docs/11/libpq-connect.html#LIBPQ-CONNECT-SSLMODE
#export POSTGRES_SSL_MODE=require
#export POSTGRES_SSL_ROOT_CERTIFICATE=/var/task/rds-combined-ca-bundle.pem

export FLASK_ENV=development

env FLASK_APP=$SRCDIR/pint_server/app.py flask run
