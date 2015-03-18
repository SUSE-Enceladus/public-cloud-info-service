# Copyright © 2015 SUSE LLC, James Mason <jmason@suse.com>.
# All Rights Reserved.
#
# THIS WORK IS SUBJECT TO U.S. AND INTERNATIONAL COPYRIGHT LAWS AND TREATIES.
# IT MAY NOT BE USED, COPIED, DISTRIBUTED, DISCLOSED, ADAPTED, PERFORMED,
# DISPLAYED, COLLECTED, COMPILED, OR LINKED WITHOUT SUSE'S PRIOR WRITTEN
# CONSENT. USE OR EXPLOITATION OF THIS WORK WITHOUT AUTHORIZATION COULD SUBJECT
# THE PERPETRATOR TO CRIMINAL AND CIVIL LIABILITY.

require 'sinatra/base'
require 'nokogiri'
require 'json'

class PublicCloudInfoSrv < Sinatra::Base
  set :root, File.dirname(__FILE__)

  ENV['RACK_ENV'] ||= 'development'
  require 'bundler'
  Bundler.require :default, ENV['RACK_ENV'].to_sym

  def self.import_framework(file_path)
    document = Nokogiri::XML(File.open(file_path))
    Hash[
      document.css('framework').collect do |framework_tag|
        [framework_tag[:name], framework_tag ] if framework_tag[:name]
      end
    ]
  end

  configure do
    set :categories, %w(servers images)
    set :extensions, %w(json xml)

    frameworks = {}
    if ENV['FRAMEWORKS']
      Dir.glob(ENV['FRAMEWORKS']).each do |path|
        frameworks.merge! import_framework(path)
      end
    end
    set :frameworks, frameworks
    set :providers, frameworks.keys
  end


  def validate_params_provider()
    settings.providers.include?(params[:provider]) || halt(404)
  end

  def validate_params_category()
    settings.categories.include?(params[:category]) || halt(404)
  end

  def validate_params_ext()
    params[:ext] ||= 'json'
    settings.extensions.include?(params[:ext]) || halt(400)
  end


  def servers(provider)
    settings.frameworks[provider].css("servers>server")
  end

  def images(provider)
    settings.frameworks[provider].css("images>image")
  end


  def responses_as_xml(category, responses)
    Nokogiri::XML::Builder.new { |xml|
      xml.send(category) {
        xml.parent << responses
      }
    }.to_xml
  end

  def responses_as_json(category, responses)
    {
      category => responses.collect { |response|
        response.attributes.to_hash
      }
    }.to_json
  end


  get '/' do
    "SUSE Public Cloud Information Server"
  end

  get '/v1/:provider/:category.?:ext?' do
    validate_params_ext
    validate_params_category
    validate_params_provider

    responses = send(params[:category], params[:provider])

    content_type params[:ext]
    case params[:ext]
    when 'json'
      responses_as_json(params[:category], responses)
    when 'xml'
      responses_as_xml(params[:category], responses)
    end
  end

  get '/*' do
    status 400
  end
end
