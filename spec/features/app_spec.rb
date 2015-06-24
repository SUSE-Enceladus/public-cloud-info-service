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


require_relative '../spec_helper'

describe 'Root Path' do
  describe 'GET /' do
    before { get '/' }

    it 'redirects permanently' do
      expect(last_response.status).to eq 301
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

  describe 'server_type' do
    describe 'valid types' do
      it 'responds successfully' do
        $valid_server_types.each do |server_type|
          get "v1/#{$valid_providers.first}/servers/#{server_type}"
        end
      end
    end

    describe 'invalid type' do
      it 'is 404 Not Found' do
        get "v1/#{$valid_providers.first}/servers/foo"
        expect(last_response.status).to eq 404
      end
    end
  end

  describe 'image_state' do
    describe 'valid states' do
      it 'responds successfully' do
        $valid_image_states.each do |image_state|
          get "v1/#{$valid_providers.first}/images/#{image_state}"
        end
      end
    end

    describe 'invalid state' do
      it 'is 404 Not Found' do
        get "v1/#{$valid_providers.first}/images/foo"
        expect(last_response.status).to eq 404
      end
    end
  end

  describe 'region' do
    describe 'valid regions' do
      it 'responds successfully' do
        $valid_regions.each do |region|
          get URI.encode(
            "v1/#{$valid_providers.first}/#{region}/#{$valid_categories.first}"
          )
        end
      end
    end
    
    describe 'invalid region' do
      it 'is 404 Not Found' do
        get "v1/#{$valid_providers.first}/foo/#{$valid_categories.first}"
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

# we comprehensively test every path here, for a given vendor
describe 'response content: /v1/microsoft' do
  before do
    @path = '/v1/microsoft'
  end

  describe '/servers' do
    before do
      @path << '/servers'
    end

    describe '.json' do
      it 'should match a defined sample' do
        @path << '.json'
        compare_with_fixture(@path)
      end
    end

    describe '.xml' do
      it 'should match a defined sample' do
        @path << '.xml'
        compare_with_fixture(@path)
      end
    end

    describe '/smt' do
      before do
        @path << '/smt'
      end

      describe '.json' do
        it 'should match a defined sample' do
          @path << '.json'
          compare_with_fixture(@path)
        end
      end

      describe '.xml' do
        it 'should match a defined sample' do
          @path << '.xml'
          compare_with_fixture(@path)
        end
      end
    end

    describe '/regionserver' do
      before do
        @path << '/regionserver'
      end

      describe '.json' do
        it 'should match a defined sample' do
          @path << '.json'
          compare_with_fixture(@path)
        end
      end

      describe '.xml' do
        it 'should match a defined sample' do
          @path << '.xml'
          compare_with_fixture(@path)
        end
      end
    end
  end

  describe '/images' do
    before do
      @path << '/images'
    end

    describe '.json' do
      it 'should match a defined sample' do
        @path << '.json'
        compare_with_fixture(@path)
      end
    end

    describe '.xml' do
      it 'should match a defined sample' do
        @path << '.xml'
        compare_with_fixture(@path)
      end
    end

    describe '/active' do
      before do
        @path << '/active'
      end

      describe '.json' do
        it 'should match a defined sample' do
          @path << '.json'
          compare_with_fixture(@path)
        end
      end

      describe '.xml' do
        it 'should match a defined sample' do
          @path << '.xml'
          compare_with_fixture(@path)
        end
      end
    end

    describe '/deprecated' do
      before do
        @path << '/deprecated'
      end

      describe '.json' do
        it 'should match a defined sample' do
          @path << '.json'
          compare_with_fixture(@path)
        end
      end

      describe '.xml' do
        it 'should match a defined sample' do
          @path << '.xml'
          compare_with_fixture(@path)
        end
      end
    end

    describe '/deleted' do
      before do
        @path << '/deleted'
      end

      describe '.json' do
        it 'should match a defined sample' do
          @path << '.json'
          compare_with_fixture(@path)
        end
      end

      describe '.xml' do
        it 'should match a defined sample' do
          @path << '.xml'
          compare_with_fixture(@path)
        end
      end
    end
  end

  describe '/West US' do
    before do
      @path << '/West US'
    end

    describe '/servers' do
      before do
        @path << '/servers'
      end

      describe '.json' do
        it 'should match a defined sample' do
          @path << '.json'
          compare_with_fixture(@path)
        end
      end

      describe '.xml' do
        it 'should match a defined sample' do
          @path << '.xml'
          compare_with_fixture(@path)
        end
      end

      describe '/smt' do
        before do
          @path << '/smt'
        end

        describe '.json' do
          it 'should match a defined sample' do
            @path << '.json'
            compare_with_fixture(@path)
          end
        end

        describe '.xml' do
          it 'should match a defined sample' do
            @path << '.xml'
            compare_with_fixture(@path)
          end
        end
      end

      describe '/regionserver' do
        before do
          @path << '/regionserver'
        end

        describe '.json' do
          it 'should match a defined sample' do
            @path << '.json'
            compare_with_fixture(@path)
          end
        end

        describe '.xml' do
          it 'should match a defined sample' do
            @path << '.xml'
            compare_with_fixture(@path)
          end
        end
      end
    end

    describe '/images' do
      before do
        @path << '/images'
      end

      describe '.json' do
        it 'should match a defined sample' do
          @path << '.json'
          compare_with_fixture(@path)
        end
      end

      describe '.xml' do
        it 'should match a defined sample' do
          @path << '.xml'
          compare_with_fixture(@path)
        end
      end

      describe '/active' do
        before do
          @path << '/active'
        end

        describe '.json' do
          it 'should match a defined sample' do
            @path << '.json'
            compare_with_fixture(@path)
          end
        end

        describe '.xml' do
          it 'should match a defined sample' do
            @path << '.xml'
            compare_with_fixture(@path)
          end
        end
      end

      describe '/deprecated' do
        before do
          @path << '/deprecated'
        end

        describe '.json' do
          it 'should match a defined sample' do
            @path << '.json'
            compare_with_fixture(@path)
          end
        end

        describe '.xml' do
          it 'should match a defined sample' do
            @path << '.xml'
            compare_with_fixture(@path)
          end
        end
      end

      describe '/deleted' do
        before do
          @path << '/deleted'
        end

        describe '.json' do
          it 'should match a defined sample' do
            @path << '.json'
            compare_with_fixture(@path)
          end
        end

        describe '.xml' do
          it 'should match a defined sample' do
            @path << '.xml'
            compare_with_fixture(@path)
          end
        end
      end
    end
  end
end
