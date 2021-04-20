all: sle15

sle15: create_staging copy_sle15_dockerfile build_image clean

aws: create_staging build_psycopg2_bin copy_dependent_libs copy_requirements_txt copy_aws_dockerfile build_image 

create_staging:
	mkdir -p .staging
	cp *.py .staging/
	cp -r pint_server .staging/

build_psycopg2_bin:
	mkdir -p .staging/opt/python/lib/python3.6/site-packages
	python -m pip install psycopg2 -t ".staging/opt/python/lib/python3.6/site-packages"

copy_dependent_libs:
ifneq ("$(wildcard /usr/lib/libpq.so.5)","")
	mkdir -p .staging/usr/lib
	cp /usr/lib/libpq.so.5 .staging/usr/lib/libpq.so.5
	cp /usr/lib/libssl.so.1.1 .staging/usr/lib/libssl.so.1.1
	cp /usr/lib/libcrypto.so.1.1 .staging/usr/lib/libcrypto.so.1.1
else
	mkdir -p .staging/usr/lib64
	cp /usr/lib64/libpq.so.5 .staging/usr/lib64/libpq.so.5
	cp /usr/lib64/libssl.so.1.1 .staging/usr/lib64/libssl.so.1.1
	cp /usr/lib64/libcrypto.so.1.1 .staging/usr/lib64/libcrypto.so.1.1
endif

copy_requirements_txt:
	cp requirements.txt .staging
	sed -i '/^psycopg2/d' .staging/requirements.txt

copy_aws_dockerfile:
	cp Dockerfile.aws .staging/Dockerfile

copy_sle15_dockerfile:
	cp Dockerfile.sle15 .staging/Dockerfile

build_image:
	sam build

clean:
	rm -rf .staging
