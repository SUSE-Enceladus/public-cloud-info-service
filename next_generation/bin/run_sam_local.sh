#!/bin/bash

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
