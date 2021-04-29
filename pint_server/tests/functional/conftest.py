# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

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
