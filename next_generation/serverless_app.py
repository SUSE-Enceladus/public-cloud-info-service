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
