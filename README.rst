============
Introduction
============

Public Cloud Information Service enables users to lookup Public Cloud
images and services information via REST API. Image and Server information
is tracked in a PostgreSQL database.

=============
Prerequisites
=============

Prior to running Pint Server, you must prepare an instance of PostgreSQL
database with the up-to-date Pint Server schema and data.

1. follow the instructions to install an instance of PostgreSQL from your
   favorite vendor
2. clone the *pint-data* repo
3. create the Python 3.6 development virtual environment

   .. code-block::

     ./bin/create_dev_venv.sh

4. activate the development virtual environment

   .. code-block::

     source dev_venv/bin/activate

5. run the *./bin/pint_db_migrate.sh* CLI to perform scheme and data upgrade.
   The script itself is idempotent so it won't fail if the schema and data
   are already up-to-date.

   .. code-block::

     ./bin/pint_db_migrate.sh -h db_host -U db_user -W db_password -n db_name --ssl-mode required --root-cert /etc/ssl/postgresql_ca_cert.pem upgrade --pint-data /home/foo/pint-data

   **NOTE**: in the above example, */home/foo/pint-data* is where you clone the
   *pint-data* repo. In other words, the XML data files are expected to be
   located in the */home/foo/pint-data/data* directory.

   **NOTE**: in a development environment where TLS is not enabled for the
   PostgreSQL instance, the *--ssl-mode* and *--root-cert* arguments are
   not needed.

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

3. update *./bin/run_standalone.sh* with the correct PostgreSQL host, user,
   password, and database name.

4. run the standalone Flask application. By default, it is listening for HTTP
   requests on port 5000.

   .. code-block::

     ./bin/run_standalone.sh

5. open a separate terminal and test it with curl command

   .. code-block::

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

3. update *./local_test_env.json* with the correct PostgreSQL host, user,
   password, and database name.

4. run serverless application

   .. code-block::

     ./bin/run_sam_local.sh

5. open a separate terminal and test it with curl command

   .. code-block::

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

Running the Load Tests Using Locust
-----------------------------------
Follow the steps below to run the locust load tests:

Pre-requisite
These load tests expect the environment under test to be setup correctly.

1. Setup a python virtual environment

   .. code-block::

     ./bin/create_test_venv.sh

2. Activate the python virtual environment created in Step 1

   .. code-block::

     source test_venv/bin/activate

3. Run the locust load tests
   For example:

   .. code-block::

     locust -f pint_server/tests/loadtest/locustfile.py  --host http://localhost:5000 --headless -u 100 -r 10

   .. code-block::

    --host is where the pint service is running
    -u specifies the number of users to spawn
    -r specifies the number of users to start per second

If you want to specify the runtime for the loadtests, you can do so with the -t option:
For example:
.. code-block::

      locust -f pint_server/tests/loadtest/locustfile.py  --host http://localhost:5000 --headless -u 100 -r 10 -t10m

=====================
How To Upgrade Schema
=====================

Here's an example of a normal workflow for performing schema update.

1. create a new changeset file in *pint_server/pint_db_migrate/versions/*. The
   new changeset file must have the following format: *<d><d><d>_<string>.py*.
   The first three digit of the filename is the version number, follow by an
   underscore and a meaningful name of the changeset. The new changeset must
   have the highest version number, which is usually a plus one increment of
   the last version. For example, if *pint_server/pint_db_migrate/versions/*
   currently contains a file *001_in_the_beginning.py*. The next changeset
   should starts with *002*. Say if we want to add a new column *foo* to the
   *amazonimages* table. We should create a new file named *002_add_foo_column_to_amazonimages.py* with the following content:

   .. code-block::

     from sqlalchemy import Table, MetaData, String, Column

     def upgrade(migrate_engine):
         meta = MetaData(bind=migrate_engine)
         amazonimages = Table('amazonimages', meta, autoload=True)
         foo = Column('foo', String(100))
         foo.create(amazonimages)

     def downgrade(migrate_engine):
         meta = MetaData(bind=migrate_engine)
         amazonimages = Table('amazonimages', meta, autoload=True)
         amazonimages.c.foo.drop()

2. create the Python 3.6 development virtual environment

   .. code-block::

     ./bin/create_dev_venv.sh

3. activate the development virtual environment

   .. code-block::

     source dev_venv/bin/activate

4. run the *./bin/pint_db_migrate.sh* CLI to perform scheme and data upgrade.
   The script itself is idempotent so it won't fail if the schema and data
   are already up-to-date.

   .. code-block::

     ./bin/pint_db_migrate.sh -h db_host -U db_user -W db_password -n db_name --ssl-mode require --root-cert /etc/ssl/postgresql_ca_cert.pem upgrade --pint-data /home/foo/pint-data

   **NOTE**: in the above example, */home/foo/pint-data* is where you clone the
   *pint-data* repo. In other words, the XML data files are expected to be
   located in the */home/foo/pint-data/data* directory.

   **NOTE**: in a development environment where TLS is not enabled for the
   PostgreSQL instance, the *--ssl-mode* and *--root-cert* arguments are
   not needed.
