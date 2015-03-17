# Copyright © 2014 SUSE LLC, James Mason <jmason@suse.com>.
# All Rights Reserved.
#
# THIS WORK IS SUBJECT TO U.S. AND INTERNATIONAL COPYRIGHT LAWS AND TREATIES.
# IT MAY NOT BE USED, COPIED, DISTRIBUTED, DISCLOSED, ADAPTED, PERFORMED,
# DISPLAYED, COLLECTED, COMPILED, OR LINKED WITHOUT SUSE'S PRIOR WRITTEN
# CONSENT. USE OR EXPLOITATION OF THIS WORK WITHOUT AUTHORIZATION COULD SUBJECT
# THE PERPETRATOR TO CRIMINAL AND CIVIL LIABILITY.

require 'sinatra/base'
require 'nokogiri'

class PublicCloudInfoSrv < Sinatra::Base
  set :root, File.dirname(__FILE__)

  ENV['RACK_ENV'] ||= 'development'
  require 'bundler'
  Bundler.require :default, ENV['RACK_ENV'].to_sym

  configure do
    set :providers,  %w(amazon google hp microsoft)
    set :categories, %w(servers images)
    set :extensions, %w(json xml)
  end

  def validate_params_provider()
    settings.providers.include?(params[:provider]) || halt(404)
  end

  def validate_params_category()
    settings.categories.include?(params[:category]) || halt(404)
  end

  def validate_params_ext()
    params[:ext] ||= 'json'
    settings.extensions.include?(params[:ext]) || halt(415)
  end

  get '/' do
    "SUSE Public Cloud Information Server"
  end

  get '/v1/:provider/:category.?:ext?' do
    validate_params_ext
    validate_params_category
    validate_params_provider
    "You asked for #{ params[:provider] }'s #{ params[:category] }, in the #{ params[:ext] } format."
  end
end
