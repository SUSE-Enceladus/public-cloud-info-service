
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