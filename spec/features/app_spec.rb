# Copyright © 2014 SUSE LLC, James Mason <jmason@suse.com>.
# All Rights Reserved.
#
# THIS WORK IS SUBJECT TO U.S. AND INTERNATIONAL COPYRIGHT LAWS AND TREATIES.
# IT MAY NOT BE USED, COPIED, DISTRIBUTED, DISCLOSED, ADAPTED, PERFORMED,
# DISPLAYED, COLLECTED, COMPILED, OR LINKED WITHOUT SUSE'S PRIOR WRITTEN
# CONSENT. USE OR EXPLOITATION OF THIS WORK WITHOUT AUTHORIZATION COULD SUBJECT
# THE PERPETRATOR TO CRIMINAL AND CIVIL LIABILITY.

require_relative '../spec_helper'

describe 'Root Path' do
  describe 'GET /' do
    before { get '/' }

    it 'is successful' do
      expect(last_response.status).to eq 200
    end
  end
end

describe 'supported version' do
  describe 'v1' do
    it 'responds successfully' do
      get "v1/#{$valid_providers.first}/#{$valid_categories.first}"
      expect(last_response.status).to eq 200
    end
  end

  describe 'any other version' do
    before { get "/v2/#{$valid_providers.first}/#{$valid_categories.first}" }
    it 'is 400 Bad Request' do
      expect(last_response.status).to eq 400
    end
    it 'returns no body' do
      expect(last_response.body).to eq ''
    end
  end
end

describe 'route validation' do
  describe 'provider' do
    describe 'valid providers' do
      it 'responds successfully' do
        $valid_providers.each do |provider|
          get "v1/#{provider}/#{$valid_categories.first}"
          expect(last_response.status).to eq 200
        end
      end
    end

    describe 'invalid providers' do
      it 'is 404 Not Found' do
        get "v1/foo/#{$valid_categories.first}"
        expect(last_response.status).to eq 404
      end
    end
  end

  describe 'category' do
    describe 'valid categories' do
      it 'responds successfully' do
        $valid_categories.each do |category|
          get "v1/#{$valid_providers.first}/#{category}"
        end
      end
    end

    describe 'invalid category' do
      it 'is 404 Not Found' do
        get "v1/#{$valid_providers.first}/foo"
        expect(last_response.status).to eq 404
      end
    end
  end

  describe 'extention' do
    describe 'valid extentions' do
      it 'responds successfully' do
        $valid_extensions.each do |ext|
          get "v1/#{$valid_providers.first}/#{$valid_categories.first}.#{ext}"
          expect(last_response.status).to eq 200
        end
      end
    end

    describe 'no extention' do
      it 'responds successfully' do
        get "v1/#{$valid_providers.first}/#{$valid_categories.first}"
        expect(last_response.status).to eq 200
      end
    end

    describe 'invalid extentions' do
      it 'is 400 Bad Request' do
        get "v1/#{$valid_providers.first}/#{$valid_categories.first}.foo"
        expect(last_response.status).to eq 400
      end
    end
  end
end

describe 'response type' do
  before do
    @path = "/v1/#{$valid_providers.first}/#{$valid_categories.first}"
  end

  describe 'Content-Type header' do
    it 'matches the supplied extension' do
      get "#{@path}.json"
      expect(last_response.content_type).to eq "application/json"

      get "#{@path}.xml"
      expect(last_response.content_type).to eq "application/xml;charset=utf-8"
    end
  end

  describe 'body' do
    it 'matches the supplied extension' do
      get "#{@path}.json"
      expect(last_response.body[0,1]).to eq "{"

      get "#{@path}.xml"
      expect(last_response.body[0,21]).to eq '<?xml version="1.0"?>'
    end
  end
end

describe 'response content' do
  before do
    @path = '/v1/microsoft/'
  end
  describe 'servers category' do
    before do
      @path << 'servers'
    end
    describe 'json format' do
      before do
        @path << '.json'
      end
      it 'should match a defined sample' do
        expected_response = IO.read(File.join(File.dirname(__FILE__), "../fixtures", @path))

        get @path
        expect(last_response.body.strip).to eq expected_response.strip
      end
    end

    describe 'xml format' do
      before do
        @path << '.xml'
      end
      it 'should match a defined sample' do
        expected_response = IO.read(File.join(File.dirname(__FILE__), "../fixtures", @path))

        get @path
        expect(last_response.body.strip).to eq expected_response.strip
      end
    end
  end

  describe 'images category' do
    before do
      @path << 'images'
    end
    describe 'json format' do
      before do
        @path << '.json'
      end
      it 'should match a defined sample' do
        expected_response = IO.read(File.join(File.dirname(__FILE__), "../fixtures", @path))

        get @path
        expect(last_response.body.strip).to eq expected_response.strip
      end
    end

    describe 'xml format' do
      before do
        @path << '.xml'
      end
      it 'should match a defined sample' do
        expected_response = IO.read(File.join(File.dirname(__FILE__), "../fixtures", @path))

        get @path
        expect(last_response.body.strip).to eq expected_response.strip
      end
    end
  end
end
