all: sle15

sle15: create_staging copy_sle15_dockerfile build_image clean

aws: create_staging copy_requirements_txt copy_aws_dockerfile build_image 

create_staging:
	mkdir -p .staging
	cp *.py .staging/
	cp -r pint_server .staging/

copy_requirements_txt:
	cp requirements.txt .staging

copy_aws_dockerfile:
	cp Dockerfile.aws .staging/Dockerfile

copy_sle15_dockerfile:
	cp Dockerfile.sle15 .staging/Dockerfile

build_image:
	sam build

clean:
	rm -rf .staging
