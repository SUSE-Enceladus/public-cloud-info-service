ENV['RACK_ENV'] = 'test'

require_relative File.join('..', 'app.rb')
require 'rspec'
require 'rack/test'

RSpec.configure do |config|
  include Rack::Test::Methods

  def app
    PublicCloudInfoSrv
  end
end
