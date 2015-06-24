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
    set :server_types, %w(smt regionserver)
    set :image_states, %w(active deprecated deleted)

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

  def validate_params_server_type()
    settings.server_types.include?(params[:server_type]) || halt(400)
  end

  def validate_params_image_state()
    settings.image_states.include?(params[:image_state]) || halt(400)
  end


  def servers(provider)
    settings.frameworks[provider].css("servers>server")
  end

  def servers_of_type(provider, server_type)
    settings.frameworks[provider].css("servers>server[type='#{server_type}']")
  end

  def servers_in_region(provider, region)
    settings.frameworks[provider].css("servers>server[region='#{region}']")
  end

  def images(provider)
    settings.frameworks[provider].css("images>image")
  end

  def images_of_state(provider, image_state)
    settings.frameworks[provider].css("images>image[state='#{image_state}']")
  end

  def images_in_region(provider, region)
    settings.frameworks[provider].css("images>image[region='#{region}']")
  end


  def responses_as_xml(category, responses)
    Nokogiri::XML::Builder.new { |xml|
      xml.send(category) {
        responses.each do |response|
          xml.parent << response.clone
        end
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

  def respond_with(format, category, responses)
    content_type format

    case format
    when 'json'
      responses_as_json(category, responses)
    when 'xml'
      responses_as_xml(category, responses)
    end
  end

  get '/' do
    "SUSE Public Cloud Information Server"
  end

  get '/v1/:provider/:category.?:ext?' do
    validate_params_ext
    validate_params_category
    validate_params_provider

    responses = send(params[:category], params[:provider])

    respond_with params[:ext], params[:category], responses
  end

  get '/v1/:provider/servers/:server_type.?:ext?' do
    validate_params_ext
    validate_params_provider
    validate_params_server_type

    responses = servers_of_type(params[:provider], params[:server_type])

    respond_with params[:ext], :servers, responses
  end

  get '/v1/:provider/images/:image_state.?:ext?' do
    validate_params_ext
    validate_params_provider
    validate_params_image_state

    responses = images_of_state(params[:provider], params[:image_state])

    respond_with params[:ext], :images, responses
  end

  get '/v1/:provider/:region/:category.?:ext?' do
    validate_params_ext
    validate_params_category
    validate_params_provider

    responses = send("#{params[:category]}_in_region", params[:provider],
      params[:region])

    respond_with params[:ext], params[:category], responses
  end

  get '/*' do
    status 400
  end
end
