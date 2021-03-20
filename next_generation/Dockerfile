FROM public.ecr.aws/lambda/python:3.6

COPY serverless_app.py app.py models.py .staging/requirements.txt ./
COPY .staging/ /

# Add AWS RDS trusted certificate chain to SSL/TLS connection to the
# RDS instance
ADD https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem /var/task/

RUN python3.6 -m pip install -r requirements.txt -t .

# Command can be overwritten by providing a different command in the template directly.
CMD ["serverless_app.handler"]
