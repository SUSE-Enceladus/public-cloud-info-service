============
Introduction
============

Public Cloud Information Service Next Generation (a.k.a. Pint Server NG) enable
users to lookup SUSE Public Cloud images and services via REST API. Public
Cloud images and servers data is expected to be managed by the (PostgreSQL)
database.

Pint Server NG is implemented as a `Python Flask application <https://flask.palletsprojects.com/en/1.1.x/>`_. The Lambda functionality is being facilitated by
the `serverless-wsgi <https://github.com/logandk/serverless-wsgi>`_ framework.

Pint Server NG is being deployed as an AWS Lambda function. Therefore, it will
be released as a container image, which is based on SLE 15.2 with
AWS Lambda Python 3.6 Runtime Interface Client (`awslambdaric <https://github.com/aws/aws-lambda-python-runtime-interface-client>`_).

===========
Quick Start
===========

There are two ways you can run Pint Server NG service locally:

1. as a standalone Flask application.
2. as a serverless application via AWS Serverless Application Model (SAM) CLI
   with the embedded Lambda runtime emulator.

The former is recommended to test the application logic with the AWS layer
baggage while the latter is good to test the Lambda function deployment
readiness. In most cases, you'll only need to test your changes by running
the standalone Flask application.

Runing Standalone Flask Application
-----------------------------------

To run the standalone Flask application:

1. create the Python 3.6 development virtual environment

   .. code-block::

     ./bin/create_dev_venv.sh

2. activate the development virtual environment

   .. code-block::

     source dev_venv/bin/activate

3. run the standalone Flask application. By default, it is listening HTTP
   requests on port 5000.

   .. code-block::

     ./bin/run_standalone.sh

4. open a separate terminal and test it with curl command

   .. code-black::

     curl http://127.0.0.1:5000/v1/providers


Running Serverless Application Locally via SAM CLI
--------------------------------------------------

To run the serverless application via SAM CLI:

1. make sure both *aws-sam-cli* Python package is installed. If not, install
   it with pip.

   .. code-block::

     sudo pip install aws-sam-cli

2. build the Pint Server NG Lambda function container image with make CLI. By
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

**NOTE:** by default, the container image is based on the SLE 15.2 base image.
However, you may choose to use the AWS base image instead, for debugging
purposes in case IBS is not accessible. To use the AWS base image:

.. code-block::

  make aws


=====================
Developing Unit Tests
=====================

Introduction
------------

For the purpose of unit testing, we are using MagicMock to handle
the DB layer and manipulate the return values.

For example:
When we mock the app.get_provider_images, in this stack:
```
Flask app API handler -> app.list_provider_resource -> app.get_provider_images -> AlibabaImagesModel -> sqlachemy -> DB driver
```
we intercept the call with our own fixtures instead of getting them from the DB.

Running The Unittests
---------------------
Follow the following steps to run these unittests:

1. Setup a python virtual environment

   .. code-block::

     ./bin/create_test_venv.sh

2. Activate the python virtual environment created in Step 1

   .. code-block::

     source test_venv/bin/activate

3. Run the unittests

   .. code-block::

     python -m pytest pint_server/tests/unit


Running the Functional Tests
------------------------------
Follow the following steps to run the functional tests:

Pre-requisite
These functional tests expect the environment under test to be setup correctly.

1. Setup a python virtual environment

   .. code-block::

     ./bin/create_test_venv.sh

2. Activate the python virtual environment created in Step 1

   .. code-block::

     source test_venv/bin/activate

3. Run the functional tests

   .. code-block::

     python -m pytest pint_server/tests/functional

By default, these tests run against https://susepubliccloudinfo.suse.com

You can pass the --base-url option to point to your pint api service.

For example:

    .. code-block::

     python -m pytest --base-url http://localhost:5000 pint_server/tests/functional

=====================
How To Make A Release
=====================

1. Update `VERSION.txt` with the appropriate version
2. Create a git tag for the last commit

