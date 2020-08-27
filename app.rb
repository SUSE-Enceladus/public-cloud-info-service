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

require 'sinatra/base'
require 'nokogiri'
require 'json'

# We extend nodeset to allow for pint-specific functions on the data
class Nokogiri::XML::NodeSet
  def in_env(environment)
    css("[environment='#{environment}']")
  end

  def in_region(region)
    css("[region='#{region}']")
  end

  def of_type(server_type)
    css("[type|='#{server_type}']")
  end

  def in_state(image_state)
    css("[state='#{image_state}']")
  end

  def set_region(region) # rubocop:disable Naming/AccessorMethodName
    each do |node|
      node.set_attribute('region', region)
    end
    return self
  end

  def clear_region
    each do |node|
      node.remove_attribute('region')
    end
    return self
  end
end

# The pint server, as a Sinatra superclass
class PublicCloudInfoSrv < Sinatra::Base
  set :root, File.dirname(__FILE__)

  ENV['RACK_ENV'] ||= 'development'

  def self.import_framework(file_path)
    document = Nokogiri::XML(File.open(file_path))
    Hash[
      document.css('framework').collect do |framework_tag|
        [framework_tag[:name], framework_tag] if framework_tag[:name]
      end
    ]
  end

  def self.collect_valid_regions(frameworks)
    Hash[
      frameworks.map do |provider, framework|
        regions = [
          framework.css('server[region],image[region]').map { |n| n['region'] },
          framework.css('region[name]').map { |n| n['name'] }
        ].flatten.compact.uniq.sort!
        [provider, regions]
      end
    ]
  end

  configure do
    set :categories,   ['servers', 'images']
    set :extensions,   ['json', 'xml']
    set :server_types, ['smt', 'regionserver']
    set :image_states, ['active', 'inactive', 'deprecated', 'deleted']

    frameworks = {}
    if ENV['FRAMEWORKS']
      Dir.glob(ENV['FRAMEWORKS']).each do |path|
        frameworks.merge! import_framework(path)
      end
    end
    set :frameworks, frameworks
    set :providers,  frameworks.keys
    set :regions,    collect_valid_regions(frameworks)
  end

  def validate_params_provider
    settings.providers.include?(params[:provider]) || halt(404)
  end

  def validate_params_category
    settings.categories.include?(params[:category]) || halt(404)
  end

  def validate_params_server_type
    settings.server_types.include?(params[:server_type]) || halt(404)
  end

  def validate_params_image_state
    settings.image_states.include?(params[:image_state]) || halt(404)
  end

  def validate_params_region
    settings.regions[params[:provider]].include?(params[:region]) || halt(404)
  end

  def validate_params_ext
    params[:ext] ||= 'json'
    settings.extensions.include?(params[:ext]) || halt(400)
  end

  def servers(provider)
    settings.frameworks[provider].css('servers>server')
  end

  def images(provider)
    settings.frameworks[provider].css('images>image')
  end

  def remap_region_to_environment(provider, region)
    # if the framework uses environments
    framework = settings.frameworks[provider]
    regions_in_env = framework.css("environment>region[name='#{region}']")
    return region if regions_in_env.empty?

    environment = regions_in_env.first.parent
    return environment['name']
  end

  def environments?(provider)
    framework = settings.frameworks[provider]
    return !framework.css('environments').empty?
  end

  def responses_as_xml(category, responses)
    Nokogiri::XML::Builder.new do |xml|
      xml.send(category) do
        responses.each do |response|
          xml.parent << response.clone
        end
      end
    end.to_xml
  end

  def responses_as_json(category, responses)
    {
      category => responses.collect do |response|
        response.attributes.to_hash
      end
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

  def form_xml_for_settings(tag, values)
    Nokogiri::XML::Builder.new do |xml|
      xml.root do
        values.each { |value| xml.send(tag, name: value) }
      end
    end.doc.css(tag)
  end

  before do
    headers 'Access-Control-Allow-Origin' => '*'
  end

  get '/v1/providers.?:ext?' do
    validate_params_ext

    responses = form_xml_for_settings('provider', settings.providers)

    respond_with params[:ext], :providers, responses
  end

  get '/v1/:provider/servers/types.?:ext?' do
    validate_params_ext
    validate_params_provider

    responses = form_xml_for_settings('type', settings.server_types)

    respond_with params[:ext], :types, responses
  end

  get '/v1/images/states.?:ext?' do
    validate_params_ext

    responses = form_xml_for_settings('state', settings.image_states)

    respond_with params[:ext], :states, responses
  end

  get '/v1/:provider/regions.?:ext?' do
    validate_params_ext
    validate_params_provider

    responses = form_xml_for_settings(
      'region', settings.regions[params[:provider]]
    )

    respond_with params[:ext], :regions, responses
  end

  get '/v1/:provider/:region/servers/:server_type.?:ext?' do
    validate_params_ext
    validate_params_server_type
    validate_params_region
    validate_params_provider

    responses = servers(params[:provider])
                .of_type(params[:server_type])
                .in_region(params[:region])

    respond_with params[:ext], :servers, responses
  end

  get '/v1/:provider/servers/:server_type.?:ext?' do
    validate_params_ext
    validate_params_server_type
    validate_params_provider

    responses = servers(params[:provider]).of_type(params[:server_type])

    respond_with params[:ext], :servers, responses
  end

  get '/v1/:provider/:region/images/:image_state.?:ext?' do
    validate_params_ext
    validate_params_image_state
    validate_params_region
    validate_params_provider

    responses = if environments?(params[:provider])
      environment = remap_region_to_environment(
        params[:provider],
        params[:region]
      )
      images(params[:provider])
        .in_state(params[:image_state])
        .in_env(environment)
        .set_region(params[:region])
    else
      images(params[:provider])
        .in_state(params[:image_state])
        .in_region(params[:region])
    end
    respond_with params[:ext], :images, responses
  end

  get '/v1/:provider/images/:image_state.?:ext?' do
    validate_params_ext
    validate_params_image_state
    validate_params_provider

    responses = images(params[:provider]).in_state(params[:image_state])
    if environments?(params[:provider])
      responses.clear_region
    end

    respond_with params[:ext], :images, responses
  end

  get '/v1/:provider/:region/:category.?:ext?' do
    validate_params_ext
    validate_params_category
    validate_params_region
    validate_params_provider

    responses = if environments?(params[:provider]) &&
                   params[:category] == 'images'

      environment = remap_region_to_environment(
        params[:provider],
        params[:region]
      )
      send(
        params[:category].to_s,
        params[:provider]
      ).in_env(environment).set_region(params[:region])
    else
      send(
        params[:category].to_s,
        params[:provider]
      ).in_region(params[:region])
    end

    respond_with params[:ext], params[:category], responses
  end

  get '/v1/:provider/:category.?:ext?' do
    validate_params_ext
    validate_params_category
    validate_params_provider

    responses = send(params[:category], params[:provider])
    if params[:category] == 'images' && environments?(params[:provider])
      responses.clear_region
    end
    respond_with params[:ext], params[:category], responses
  end

  get '/' do
    redirect 'https://www.suse.com/solutions/public-cloud/', 301
  end

  get '/*' do
    status 400
  end
end
