#
# spec file for package python-PintServer
#
# Copyright (c) 2021 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%if 0%{?suse_version} >= 1600
%define pythons %{primary_python}
%else
%{?sle15_python_module_pythons}
%endif
%global _sitelibdir %{%{pythons}_sitelib}

Name:           python-PintServer
<<<<<<< gzip_compress
Version:        2.0
Release:        16
=======
Version:        2.0.16
Release:        0
>>>>>>> master
Summary:        Pint Server
License:        Apache-2.0
Group:          Development/Languages/Python
URL:            https://github.com/SUSE-Enceladus/public-cloud-info-service
Source:         pint-server-2.0.16.tar.gz
BuildRequires:  %{pythons}-pbr
BuildRequires:  %{pythons}-dateutil
BuildRequires:  %{pythons}-Flask
BuildRequires:  %{pythons}-Flask-Cors
BuildRequires:  %{pythons}-Flask-SQLAlchemy
BuildRequires:  %{pythons}-lxml
BuildRequires:  %{pythons}-mock
BuildRequires:  %{pythons}-pytest
BuildRequires:  %{pythons}-requests
BuildRequires:  %{pythons}-setuptools
BuildRequires:  python-pint-models
Requires:	%{pythons}-pbr
Requires:	%{pythons}-boto3
Requires:	%{pythons}-botocore
Requires:	%{pythons}-dateutil
Requires:	%{pythons}-click
Requires:	%{pythons}-Flask
Requires:	%{pythons}-Flask-Cors
Requires:	%{pythons}-Flask-SQLAlchemy
Requires:	%{pythons}-itsdangerous
Requires:	%{pythons}-Jinja2
Requires:	%{pythons}-jmespath
Requires:	%{pythons}-MarkupSafe
Requires:	%{pythons}-psycopg2
Requires:	%{pythons}-python-dateutil
Requires:	%{pythons}-s3transfer
Requires:	%{pythons}-six
Requires:	%{pythons}-SQLAlchemy
Requires:	%{pythons}-urllib3
Requires:	%{pythons}-Werkzeug
Requires:	python-pint-models
BuildArch:      noarch

%description
Pint Server (Python Flask) application along with
serverless-wsgi to facilitate AWS Lambda functionality.

%prep
%setup -q -n pint-server-%{version}

%build
%python_build

%install
%python_install
# install serverless-app to /var/task
install -m 0755 -d %{buildroot}/var/task
install -m 0755 serverless_app.py %{buildroot}/var/task/

%check
%pytest pint_server/tests/unit

%files 
%license LICENSE
%doc README.rst
%{_sitelibdir}/pint_server*
%{_sitelibdir}/pint_server-%{version}-py*.egg-info
%dir /var/task
/var/task/serverless_app.py

%changelog

