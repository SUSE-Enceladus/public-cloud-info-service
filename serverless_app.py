# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

# See https://www.serverless.com/plugins/serverless-wsgi

import boto3
import os


# NOTE(gyee): if neither POSTGRES_PASSWORD and DATABASE_URI are specified,
# we assume this is production deployment in AWS where the PostgresSQL
# authentication must be done via IAM. See
# https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html
if 'POSTGRES_PASSWORD' not in os.environ and 'DATABASE_URI' not in os.environ:
    rds_client = boto3.client('rds')
    auth_token = rds_client.generate_db_auth_token(
        os.environ['POSTGRES_HOST'], 5432, os.environ['POSTGRES_USER'])
    os.environ['POSTGRES_PASSWORD'] = auth_token


from pint_server import app
import serverless_wsgi


# If you need to send additional content types as text, add then directly
# to the whitelist:
#
# serverless_wsgi.TEXT_MIME_TYPES.append("application/custom+json")


def handler(event, context):
    return serverless_wsgi.handle_request(app.app, event, context)
