==========
Deployment
==========

Pint Server is implemented as a `Python Flask application <https://flask.palletsprojects.com/en/1.1.x/>`_. The Lambda functionality is being facilitated by
the `serverless-wsgi <https://github.com/logandk/serverless-wsgi>`_ framework.

Pint Server is being deployed as an AWS Lambda function. Therefore, it will
be released as a container image, which is based on SLE 15.2 with
AWS Lambda Python 3.6 Runtime Interface Client (`awslambdaric <https://github.com/aws/aws-lambda-python-runtime-interface-client>`_).

=========
Packaging
=========

Pint Server will be release as a typical Python package *python-PintServerNG*.
In order to deploy it to AWS Lambda, we'll also need to package it as a
container along with AWS Lambda Python runtime client. All the relevant
packages are managed in the *Devel:PubCloud:ProductionServices:pint* project
in `IBS <https://build.suse.de/project/show/Devel:PubCloud:ProductionServices:pint>_`.

====================================================
Testing Pint Server Lamba Function Container Locally
====================================================

1. make sure both *aws-sam-cli* Python package is installed. If not, install
   it with pip.

   .. code-block::

     sudo pip install aws-sam-cli

2. modify Dockerfile.sle15 file to include any local changes if necessary

3. build the Pint Server Lambda function container image with make CLI. By
   default, the container image is based on the SLE 15.2 base image.

   .. code-block::

     make

3. run serverless application

   .. code-block::

     ./bin/run_sam_local.sh

4. open a separate terminal and test it with curl command

   .. code-black::

     curl http://127.0.0.1:5000/v1/providers

**NOTE:** to run the serverless application in debug mode, you can use the `--debug` flag. For example:

.. code-block::

  ./bin/run_sam_local.sh --debug

=====================
How To Make A Release
=====================

1. update pint_server/__init__.py '__VERSION__' attribute with the new version

2. create a git annotated tag for the release version. For example:

   .. code-block::

     git tag -a v2.0.0 -m "Release 2.0.0"
     git push --tags

3. checkout the *python-PintServer* package in
   *Devel:PubCloud:ProductionServices:pint*.

   .. code-block::

     isc bco Devel:PubCloud:ProductionServices:pint python-PintServer

4. update both the *version* and *revision* values in the *_service* file

5. update *python-PintServer.spec* with the new version and release

6. submit the changes

