============
Introduction
============

Public Cloud Information Service enables users to lookup Public Cloud
images and services information via REST API. Image and Server information
is tracked in a PostgreSQL database.

===========
Quick Start
===========

There are two ways you can run Pint Server service locally:

1. as a standalone Flask application.
2. as a serverless application via AWS Serverless Application Model (SAM) CLI
   with the embedded Lambda runtime emulator.

The former is recommended to test the application logic without the AWS layer
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

3. run the standalone Flask application. By default, it is listening for HTTP
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

2. build the Pint Server Lambda function container image with *make*. By
   default, the container image is based on the SLES 15.2 base image.

   .. code-block::

     make aws

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
Follow the steps below to run the functional tests:

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

To run the functional tests in a loop for a specified amount of time:

You can pass the options like --minutes, --hours, --seconds to pytest

    .. code-block::
    python -m pytest --minutes 15 --base-url http://localhost:5000 pint_server/tests/functional
