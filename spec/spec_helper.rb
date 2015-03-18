# Copyright © 2014 SUSE LLC, James Mason <jmason@suse.com>.
# All Rights Reserved.
#
# THIS WORK IS SUBJECT TO U.S. AND INTERNATIONAL COPYRIGHT LAWS AND TREATIES.
# IT MAY NOT BE USED, COPIED, DISTRIBUTED, DISCLOSED, ADAPTED, PERFORMED,
# DISPLAYED, COLLECTED, COMPILED, OR LINKED WITHOUT SUSE'S PRIOR WRITTEN
# CONSENT. USE OR EXPLOITATION OF THIS WORK WITHOUT AUTHORIZATION COULD SUBJECT
# THE PERPETRATOR TO CRIMINAL AND CIVIL LIABILITY.

ENV['RACK_ENV'] = 'test'
ENV['FRAMEWORKS'] = File.expand_path(File.join(File.dirname(__FILE__), "fixtures/framework-*.xml"))

require_relative File.join('..', 'app.rb')
require 'rspec'
require 'rack/test'

RSpec.configure do |config|
  include Rack::Test::Methods

  def app
    PublicCloudInfoSrv
  end
end

$valid_providers  = %w(amazon google hp microsoft)
$valid_categories = %w(images servers)
$valid_extensions = %w(json xml)
