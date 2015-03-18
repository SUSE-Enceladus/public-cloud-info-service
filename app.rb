# Copyright © 2015 SUSE LLC, James Mason <jmason@suse.com>.
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
