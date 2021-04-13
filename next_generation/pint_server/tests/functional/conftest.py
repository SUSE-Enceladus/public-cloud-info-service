import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default='https://susepubliccloudinfo.suse.com',
        #default='http://localhost:5000',
        help="base url of the pint service"
    )

@pytest.fixture(scope="session")
def baseurl(request):
    p = request.config.getoption("--base-url")
    return p
