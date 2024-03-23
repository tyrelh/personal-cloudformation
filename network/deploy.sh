#! /bin/bash

aws cloudformation deploy --template-file network.yml --stack-name network --capabilities CAPABILITY_IAM --region ca-west-1
