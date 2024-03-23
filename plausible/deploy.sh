#! /bin/bash

aws cloudformation deploy --template-file plausible-server.yml --stack-name plausible --capabilities CAPABILITY_IAM --region ca-west-1
