# frozen_string_literal: true

require 'rspec/core/rake_task'
require 'bundler'
require 'net/http'
require 'uri'
require 'fileutils'

task default: ['specs']

RSpec::Core::RakeTask.new :specs do |task|
  task.pattern = Dir['spec/**/*_spec.rb']
end

namespace :gems do
  task :unlock, [:env] do |_task, args|
    if args.env
      rm "Gemfile.#{args.env}.lock"
    else
      rm Dir.glob('Gemfile.*.lock')
    end
  end

  task :lock, [:env] => [:unlock] do |_task, args|
    if args.env
      system "bundle install --local --gemfile=Gemfile.#{args.env}"
    else
      Dir.glob('Gemfile.*').each do |gemfile|
        system "bundle install --local --gemfile=#{gemfile}"
      end
    end
  end

  task :rpmlist, [:ruby_version, :env] do |_task, args|
    ruby_version = args.ruby_version || RUBY_VERSION.split('.')[0, 2].join('.')
    filenames = if args.env
      ["Gemfile.#{args.env}.lock"]
    else
      Dir.glob('Gemfile.*.lock')
    end
    filenames.each do |filename|
      puts "#{filename}:"
      gemspecs(filename).each do |gemspec|
        puts "\truby#{ruby_version}-rubygem-#{gemspec.name}"
      end
    end
  end

  namespace :rpmspec do
    task :requires do |_task|
      puts 'BuildRequires:  ruby-macros >= 5'
      puts 'Requires:  %{ruby}'
      gemspecs('Gemfile.production.lock').each do |gemspec|
        puts "Requires:  %{rubygem #{gemspec}}"
      end
    end
  end
end

namespace :obs do
  task :tar do |_task|
    app = ['app.rb', 'config.ru']
    configs = ['publicCloudInfo-server.conf.template']
    docs = ['LICENSE', 'README.md']
    mkdir name_version
    cp (app + configs + docs), "#{name_version}/"
    system "tar cjvf #{tarball_filename} #{name_version}"
    rm_rf name_version
    system "ls -la #{tarball_filename}"
  end

  task :cp, [:dest] => [:tar] do |_task, args|
    sources = [tarball_filename, Dir.glob('*.spec')].flatten
    cp sources, "#{args.dest}/"
    rm tarball_filename
    puts "\nNext steps:\ncd #{args.dest}; osc build ..."
  end
end

namespace :fixtures do
  task :fetch, [:path] do |_task, args|
    url = "http://localhost:9292#{URI.escape(args.path)}"
    FileUtils.mkdir_p('spec/fixtures' + args.path.split('/')[0..-2].join('/'))
    File.open("spec/fixtures#{args.path}", 'w') do |file|
      file.write Net::HTTP.get_response(URI.parse(url)).body
    end
  end
end

def gemspecs(gemfile)
  ENV['BUNDLE_GEMFILE'] = gemfile
  lockfile = Bundler::LockfileParser.new(Bundler.read_file(gemfile))
  lockfile.specs.collect(&:name).sort
end

def name_version
  @name_version ||= `rpm -q --specfile --qf '%{NAME}-%{VERSION}' *.spec`
end

def tarball_filename
  "#{name_version}.tar.bz2"
end
