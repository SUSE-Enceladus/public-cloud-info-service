all: build_psycopg2_bin copy_dependent_libs copy_requirements_txt build_image cleanup

build_psycopg2_bin:
	mkdir -p .staging/opt/python/lib/python3.6/site-packages
	python -m pip install psycopg2 -t ".staging/opt/python/lib/python3.6/site-packages"

copy_dependent_libs:
	mkdir -p .staging/usr/lib64
	cp /usr/lib64/libpq.so.5 .staging/usr/lib64/libpq.so.5
	cp /usr/lib64/libssl.so.1.1 .staging/usr/lib64/libssl.so.1.1
	cp /usr/lib64/libcrypto.so.1.1 .staging/usr/lib64/libcrypto.so.1.1

copy_requirements_txt:
	cp requirements.txt .staging
	sed -i '/^psycopg2/d' .staging/requirements.txt

build_image:
	sam build

cleanup:
	rm -rf .staging
