require 'sinatra/base'
require 'nokogiri'

class PublicCloudInfoSrv < Sinatra::Base

  set :root, File.dirname(__FILE__)

  ENV['RACK_ENV'] ||= 'development'
  require 'bundler'
  Bundler.require :default, ENV['RACK_ENV'].to_sym


  get '/' do
    "Hello World!"
  end

end
