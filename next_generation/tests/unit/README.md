Unitests for the new Public Cloud Info Service
=============================================

Introduction
=============================================

For the purpose of unit testing, we are using MagicMock to handle
the DB layer and manipulate the return values. 

For example:
When we mock the app.get_provider_images, in this stack:
```
Flask app API handler -> app.list_provider_resource -> app.get_provider_images -> AlibabaImagesModel -> sqlachemy -> DB driver
```
we intercept the call with our own fixtures instead of getting them from the DB.

Steps to run unittests:
=============================================
Follow the following steps to run these unittests:

Step 1: Setup a python virtual environment
```python3 -m venv unit_test_venv```

Step 2: Activate the python virtual environment created in Step 1
```source unit_test_venv/bin/activate```

Step 3: Install the packages in this virtual env
```pip install -r next_generation/tests/unit/test-requirements```

Step 4: Run the tests
```
cd next_generation/tests/unit
python -m pytest -s -v test_app.py
```
