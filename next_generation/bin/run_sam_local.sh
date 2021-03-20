#!/bin/bash

MYNAME=$0
CURRENTDIR=$(dirname $(readlink -e $MYNAME))
# get the source code directory
SRCDIR=$(dirname $CURRENTDIR)

sam local start-api --env-vars $SRCDIR/local_test_env.json
