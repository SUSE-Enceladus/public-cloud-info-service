|CI-Workflow-Badge|

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
3. OPTIONAL: create the Python 3.6 development virtual environment. Skip this
   step if you are using an existing environment.

   .. code-block::

     ./bin/create_dev_venv.sh

4. activate the development virtual environment

   .. code-block::

     source dev_venv/bin/activate

5. OPTIONAL: skip this step if you are using a brand new virtual environment.
   Otherwise, keep the existing virtual environment up-to-date by running:

   .. code-block::

     pip install -r requirements.txt

6. run the *./bin/schema_upgrade.sh* CLI to perform scheme migration.
   The script itself is idempotent so it won't fail if the schema is
   already up-to-date.

   .. code-block::

     ./bin/schema_upgrade.sh -h db_host -U db_user -W db_password -n db_name --ssl-mode require --root-cert /etc/ssl/postgresql_ca_cert.pem upgrade

   **NOTE**: in a development environment where TLS is not enabled for the
   PostgreSQL instance, the *--ssl-mode* and *--root-cert* arguments are
   not needed.

7. run the *./bin/data_update.sh* CLI to perform data update.
   The script itself is idempotent so it won't fail if the data is
   already up-to-date.

   .. code-block::

     ./bin/data_update.sh -h db_host -U db_user -W db_password -n db_name --ssl-mode require --root-cert /etc/ssl/postgresql_ca_cert.pem update --pint-data /home/foo/pint-data

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

Overview
--------

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

We are using Alembic framework to facility schema migration. For more details,
see https://alembic.sqlalchemy.org/en/latest/tutorial.html.

Here's an example of a normal workflow for performing schema update.

1. create the Python 3.6 development virtual environment

   .. code-block::

     ./bin/create_dev_venv.sh

2. activate the development virtual environment

   .. code-block::

     source dev_venv/bin/activate

3. update `pint_server/models.py` to reflect the latest changes

4. copy `pint_server/alembic.ini.sample` to `pint_server/alembic.ini`

   .. code-block::

     cp pint_server/alembic.ini.sample pint_server/alembic.ini

5. uncomment and set the `sqlalchemy.url` property in
   `pint_server/alembic.ini` to point to database to which to generate the
   next version of the schema. Make sure the database scheme is up-to-date
   prior to generate the next revision.

   **NOTE**: if your database password contains a percent character (%), make
   sure to escape it by replacing it with two percent characters (%%).

6. auto generate the next revision. Note that Alembic will use the existing
   database as the baseline to generate the next revision so make sure the
   existing database is up-to-date. To auto generate the next revision:

   .. code-block::

   cd public-cloud-info-service/pint_server
   alembic revision --autogenerate -m 'add some table'

   If the above command is successful, you'll see the auto generate
   revision file in `./pint_db_migrate/versions/`. The file is named
   `<revision>_add_some_table.py`.

7. *IMPORTANT:* the auto-generated migration script may not have everything
   you need. Make sure to read the code carefully and make the necessary
   changes in order to complete the code.

8. run *./bin/schema_upgrade.sh* and *./bin/data_update.sh* to perform scheme
   migration and data update respectively. The scripts themselves are
   idempotent so it won't fail if the schema and data are already up-to-date.

   .. code-block::

     ./bin/schema_upgrade.sh -h db_host -U db_user -W db_password -n db_name --ssl-mode require --root-cert /etc/ssl/postgresql_ca_cert.pem upgrade
     ./bin/data_update.sh -h db_host -U db_user -W db_password -n db_name --ssl-mode require --root-cert /etc/ssl/postgresql_ca_cert.pem update --pint-data /home/foo/pint-data

   **NOTE**: in the above example, */home/foo/pint-data* is where you clone the
   *pint-data* repo. In other words, the XML data files are expected to be
   located in the */home/foo/pint-data/data* directory.

   **NOTE**: The --root-cert is path to the file with the RDS CA bundle which can be obtained from
   https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem

   **NOTE**: in a development environment where TLS is not enabled for the
   PostgreSQL instance, the *--ssl-mode* and *--root-cert* arguments are
   not needed.

Testing Schema Upgrades
-----------------------

Once you have developed a schema upgrade, to verify that it works correctly
you will need to perform the following validation steps:

1. Create a DB instance using the old schema, populated with representative
   data, either real or synthesised.

2. Pick a set of representative entries in any tables that are affected by
   the schema migration and stash their contents for later comparison.
   Similarly run some representative queries against the pint-server REST
   API, and stash the results for later comparison.

3. Perform the schema migration on the DB and validate that the migration
   worked correctly, e.g.
   * any new columns that were added have the expected values (if not null)
   * deleted columns have been removed
   * additional tables and associated resources (e.g. sequences or primary keys) have been added
   * removed tables and associated resources (e.g. sequences or primary keys) are no longer present
   * renamed tables and any associated resources (e.g. sequences or primary keys) have been renamed correctly
   * primary key definitions have been updated/removed.

4. Check that the contents of the representative rows in the relevant tables
   have the equivalent contents, allowing for schema migration, to what was
   there before the migration.  Similarly verify that the pint-server REST
   API returns equivalent results for those queries whose results were saved.

5. Test that new rows to the affected tables works as expect, thus verifying
   that any validators are working correctly after the schema migration.

.. |CI-Workflow-Badge| image:: https://github.com/SUSE-Enceladus/public-cloud-info-service/actions/workflows/ci-workflow.yml/badge.svg
  :target: https://github.com/SUSE-Enceladus/public-cloud-info-service/actions/workflows/ci-workflow.yml
  :alt: CI Workflow status - Github Actions
