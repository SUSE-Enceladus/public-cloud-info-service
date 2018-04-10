#
# spec file for package publicCloudInfo-server
# this code base is under development
#
# Copyright (c) 2015 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugzilla.suse.com/
#

Name:      publicCloudInfo-server
Version:   1.2.1
Release:   0
License:   GPL-3.0
Summary:   Server for a RESTful API to SUSE public cloud resources
URL:       http://www.github.com/SUSE/pubcloud
Group:     Productivity/Networking/Web/Servers
Source0:   %{name}-%{version}.tar.bz2
BuildRequires:  ruby-macros >= 5
Requires:  %{ruby}
Requires:  %{rubygem nokogiri}
Requires:  %{rubygem sinatra}
Requires:  rubygem-passenger-apache2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch

%description
Customers may have their networks configured such that outgoing connections are
not possible. However, they do want to allow access to our update servers.
Therefore, customers are interested to get the IP addresses of our
infrastructure servers to allow traffic to those systems.

publicCloudInfo provides a RESTful API, returning JSON and XML data, about
infrastructure servers in the public cloud, and the status of images published
in the public cloud, including deprecation status.


%prep
%setup


%build


%install
install -m 0755 -d %{buildroot}/srv/www/%{name}/public
install -m 0644 app.rb config.ru %{buildroot}/srv/www/%{name}/
install -m 0755 -d %{buildroot}/etc/apache2/vhosts.d/
install -m 0644 publicCloudInfo-server.conf.template %{buildroot}/etc/apache2/vhosts.d/


%files
%defattr(-,root,root,-)
%doc README.md LICENSE
%config /etc/apache2/vhosts.d/publicCloudInfo-server.conf.template
%defattr(-,wwwrun,www,-)
/srv/www/%{name}
%dir /etc/apache2
%dir /etc/apache2/vhosts.d


%changelog
