# frozen_string_literal: true

# Copyright (c) 2015 SUSE LLC, James Mason <jmason@suse.com>.
#
# This file is part of publicCloudInfoSrv.
#
# publicCloudInfoSrv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# publicCloudInfoSrv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with publicCloudInfoSrv. If not, see <http://www.gnu.org/licenses/>.

ENV['RACK_ENV'] = 'test'
ENV['FRAMEWORKS'] = File.expand_path(
  File.join(
    File.dirname(__FILE__),
    'fixtures/pint-data/data/frameworks.xml'
  )
)

require 'rspec'
require 'rack/test'
require 'uri'
require_relative File.join('..', 'app.rb')

RSpec.configure do |_config|
  include Rack::Test::Methods

  def app
    PublicCloudInfoSrv
  end
end

def valid_providers
  ['amazon', 'google', 'microsoft', 'oracle']
end

def valid_categories
  ['images', 'servers']
end

def valid_extensions
  ['json', 'xml']
end

def valid_server_types
  ['smt', 'regionserver']
end

def valid_image_states
  ['active', 'inactive', 'deprecated', 'deleted']
end

def valid_regions
  ['West US', 'Australia East']
end

def compare_with_fixture(path)
  expected_response = IO.read(
    File.join(
      File.dirname(__FILE__),
      'fixtures',
      path
    )
  )
  get URI.encode(path)
  unless last_response.body.strip == expected_response.strip
    puts "\nPath:\n#{path}"
    puts "Response:\n#{last_response.body.strip}"
    puts "Fixture:\n#{expected_response.strip}\n"
  end
  expect(last_response.body.strip).to eq expected_response.strip
end
