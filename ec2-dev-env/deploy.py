import sys
sys.path.append("../")
from deployutils import run_process

command = "aws cloudformation --help"
run_process(command)
