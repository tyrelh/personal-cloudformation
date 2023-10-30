import sys
sys.path.append("../")
from deployutils import run_process

template_file = "ec2-dev-env.yml"
stack_name = "dev-env"

command = f"aws cloudformation deploy --template-file {template_file} --stack-name {stack_name} --parameter-overrides 'ProjectTag=DevEnv'"
run_process(command)
