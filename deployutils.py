import sys, re, os, time, json, pickle, shlex, subprocess, boto3

# Shared values
AWS_ACCOUNT = "dev"
AWS_ACCOUNT_ID = ""
VALID_AWS_ACCOUNTS= [
  "dev",
  "production",
]
ENVIRONMENT = "dev"
VALID_ENVIRONMENTS = [
  "dev",
  "preprod",
  "testbed",
  "production"
]
AWS_ROLE_ARN = "arn:aws:iam::{aws_account}:role/GiftbitCloudformationManagementRole"
PARAMETERS = {}
PARAMETER_KEYS = []
AWS_ACCOUNT_KEY = "aws_account"
ENVIRONMENT_KEY = "environment"

# Config
PROD_AWS_ACCOUNT_ID_LAST_2 = 28
CRED_STICK_ERROR_MSG = "Ensure you have the correct credentials stick mounted"
YES_STRINGS = ["yes", "y"]
NO_STRINGS = ["no", "n"]
AWS_CONFIG_FILE_PATH = os.path.expanduser("~/.aws/config")
AWS_CREDENTIALS_FILE_PATH = os.path.expanduser("/Volumes/credentials/credentials")

def welcome_msg(stack_name_readable):
  print(f"\n\nWelcome to the {stack_name_readable} Deployment Wizard!\n")

def welcome_msg(stack_name_readable):
  global PARAMETERS, PARAMETER_KEYS
  print(f"\n\nWelcome to the {stack_name_readable} Deployment Wizard!")
  if PARAMETERS:
    print(f" ↪ This script lets you optionally pass values via CLI args to skip the Wizard.\n ↪ The argument order is {PARAMETER_KEYS}")

def is_production():
  return AWS_ACCOUNT == "production" or ENVIRONMENT == "production"

def check_for_cli_args(expected_number_of_args):
  if len(sys.argv) == expected_number_of_args + 1:
    print(f"✅ Args provided: {sys.argv[1:]}")
    return sys.argv[1:]
  return []

def create_parameters_object(keys):
  global PARAMETERS, PARAMETER_KEYS
  for key in keys:
    PARAMETERS[key] = ""
  PARAMETER_KEYS = keys

def set_parameters_from_args(args):
  global AWS_ACCOUNT_KEY, ENVIRONMENT_KEY
  print(f"✅ Parsing args as {PARAMETER_KEYS}")
  for index, key in enumerate(PARAMETER_KEYS):
    if key == AWS_ACCOUNT_KEY:
      set_aws_account(args[index])
    elif key == ENVIRONMENT_KEY:
      set_environment(args[index])
    else:
      PARAMETERS[key] = args[index]

def is_production(env = None):
  if (env):
    return env == "production"
  global AWS_ACCOUNT, ENVIRONMENT
  return AWS_ACCOUNT == "production" or ENVIRONMENT == "production"

def get_aws_account():
  global AWS_ACCOUNT
  return AWS_ACCOUNT

def set_aws_account(account):
  global AWS_ACCOUNT, VALID_AWS_ACCOUNTS
  if not string_in_list_validator(account, VALID_AWS_ACCOUNTS):
    print(f"❌ AWS Account provided ({account}) isn't valid. (possible values: {VALID_AWS_ACCOUNTS})")
    exit_with_code(1)
  if not does_aws_account_match(account):
    print(f"❌ AWS Account provided ({account}) doesn't match your credentials.")
    exit_with_code(1)
  AWS_ACCOUNT = account
  print(f"✅ AWS Account set to {AWS_ACCOUNT}")
  configure_aws_account_id()

def set_environment(env):
  global ENVIRONMENT, VALID_ENVIRONMENTS
  if env_validator(env, VALID_ENVIRONMENTS):
    ENVIRONMENT = env
    if not does_aws_account_match():
      print("❌ Environment provided doesn't match credentials")
      exit_with_code(1)
    print(f"✅ Environment set to {ENVIRONMENT}")
  else:
    print(f"❌ Environemnt provided isn't valid. (possible values: {VALID_ENVIRONMENTS})")
    exit_with_code(1)

def does_aws_account_match(env = None):
  aws_account_id = get_aws_account_id()
  last_2 = int(str(aws_account_id)[-2:])
  if is_production(env):
    return last_2 == PROD_AWS_ACCOUNT_ID_LAST_2
  else:
    return last_2 != PROD_AWS_ACCOUNT_ID_LAST_2

def get_aws_account_id():
  output = run_process_sync_in_background_return_result('aws sts get-caller-identity --query "Account" --output text')
  if "Unable to locate credentials" in output:
    print(CRED_STICK_ERROR_MSG)
    exit(1)
  return int(output.split("'")[1].strip("\\n"))

def configure_aws_account():
  global AWS_ACCOUNT_ID, AWS_ACCOUNT, AWS_ROLE_ARN, VALID_AWS_ACCOUNTS
  if len(VALID_AWS_ACCOUNTS) > 1:
    AWS_ACCOUNT = ask_for_override(
      "Which AWS account are you deploying to?",
      AWS_ACCOUNT,
      env_validator,
      VALID_AWS_ACCOUNTS
    )
  elif len(VALID_AWS_ACCOUNTS) == 1:
    AWS_ACCOUNT = VALID_AWS_ACCOUNTS[0]
  print(f"✅ Setting AWS Account to {AWS_ACCOUNT}")
  if not does_aws_account_match(AWS_ACCOUNT):
    print(f"❌ Credentials don't match account {AWS_ACCOUNT}")
    exit_with_code(1)
  configure_aws_account_id()

def configure_environment():
  global VALID_ENVIRONMENTS, ENVIRONMENT, AWS_ACCOUNT_ID, AWS_ROLE_ARN, AWS_ACCOUNT
  if len(VALID_ENVIRONMENTS) > 1:
    ENVIRONMENT = ask_for_override(
      "First, which environment are you deploying to?",
      ENVIRONMENT,
      env_validator,
      VALID_ENVIRONMENTS
    )
  elif len(VALID_ENVIRONMENTS) == 1:
    ENVIRONMENT = VALID_ENVIRONMENTS[0]
  print(f"✅ Setting environment to {ENVIRONMENT}")
  set_aws_account_for_env()
  if not does_aws_account_match(ENVIRONMENT):
    print(f"❌ Credentials don't match environment {ENVIRONMENT}")
    exit_with_code(1)
  configure_aws_account_id()

def configure_aws_account_id():
  global AWS_ACCOUNT_ID, AWS_ROLE_ARN
  AWS_ACCOUNT_ID = get_aws_account_id()
  print(f"🟢 AWS Account ID is {AWS_ACCOUNT_ID}")
  AWS_ROLE_ARN = AWS_ROLE_ARN.format(aws_account=AWS_ACCOUNT_ID)
  print(f"🟢 Using IAM Role {AWS_ROLE_ARN}")

def set_aws_account_for_env():
  global AWS_ACCOUNT
  if is_production():
    AWS_ACCOUNT = "production"
  else:
    AWS_ACCOUNT = "dev"


def run_process_sync_in_background_return_result(command):
  p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  (output, err) = p.communicate()
  p_status = p.wait()
  return str(output)


def run_process(command):
  print("\nCommand:")
  print(command, "\n")
  process = subprocess.Popen(
    shlex.split(command), 
    stdout=subprocess.PIPE,
    universal_newlines=True
  )
  while True:
    output = process.stdout.readline()
    print(output.strip())
    # Do something else
    return_code = process.poll()
    if return_code is not None:
      print(f"{'🟢' if return_code == 0 else '❗️'} CODE: {return_code}\n")
      # Process has finished, read rest of the output 
      for output in process.stdout.readlines():
        print(output.strip())
      return return_code

def exit_with_code(code):
  if code == 0:
    print("✅ Complete.")
  else:
    print("❌ There was an issue.")
  exit(code)


def exists_lambda_config(function_name):
  file_path = f"{function_name}/config.yml"
  return os.path.exists(file_path)

def read_lambda_config(function_name):
  file_path = f"{function_name}/config.yml"
  delimiter = ":"
  config = {}
  if exists_lambda_config(function_name):
    print(f"Fetching lambda config at {file_path}")
    with open(file_path, "r") as file:
      for line in file:
        key, value = list(map(lambda value: value.strip(), line.split(delimiter)))
        config[key] = value
  else:
    print(f"No config file found at {file_path}")
  print("Lambda config: ", json.dumps(config, indent=2), "\n")
  return config


def cache_data(key, data):
  file_name = f"cache-{key}.pkl"
  if os.path.exists(file_name):
    os.remove(file_name)
    print(f"🗑️ Deleted existing cache at {file_name}")
  with open(file_name, "wb") as file:
    pickle.dump(data, file)
  print(f"✅ Data cached to {file_name}\n")

def read_cache_data(key):
  file_name = f"cache-{key}.pkl"
  if os.path.exists(file_name):
    cached_data = {}
    with open(file_name, "rb") as file:
      cached_data = pickle.load(file)
    print(f"\n✅ Read cached data from {file_name}\n")
    return cached_data
  print("\nNo cache to read from\n")
  return {}

def ask_to_use_cached_data(cached_data):
  if cached_data:
    time.sleep(0.1)
    print(json.dumps(cached_data, indent=2))
    time.sleep(0.1)
    proceed_with_wizard = ask_for_override(
      f"Would you like to use the above options from a previous run of this script and skip the wizard?", 
      "yes",
      y_n_validator
    )
    return validate_yes_string(proceed_with_wizard)
  return False


def ask_for_override(msg, default_value, validator = None, valid_inputs = []):
  allowable_inputs_feedback = ""
  if len(valid_inputs) > 0:
    allowable_inputs_feedback = " (allowable values: " + ", ".join(valid_inputs).rstrip(", ") + ")"

  default_value_feedback = ""
  if (default_value):
    default_value_feedback =  f" (default: {default_value})"
  
  # request value from user
  input_value = input("\n"+msg + allowable_inputs_feedback + default_value_feedback + " ")

  if input_value == "": # user accepted default value
    return default_value
  if validator == None and len(valid_inputs) == 0: # value doesn't require validation
    return input_value
  
  # input needs validation
  input_is_valid = validator(input_value, valid_inputs)
  while input_is_valid is False:
    # ask user again for an input
    input_value = input(f"❌ \"{input_value}\" isn't a valid value here. Try again." + allowable_inputs_feedback + default_value_feedback + " ")
    if input_value == "": # user accepted default value
      break
    input_is_valid = validator(input_value, valid_inputs)
  if input_is_valid:
    return input_value
  return default_value # if for some reason above code doesn't produce a result, return default value


def int_validator(min):
  if isinstance(min, int) or isinstance(min, str) and min.isdigit():
    def curry(value, _):
      if isinstance(value, str) and value.isdigit() and int(value) >= int(min):
        return True
      return False
    return curry

def y_n_validator(value, _):
  return isinstance(value, str) and value.lower().strip() in YES_STRINGS + NO_STRINGS

def validate_yes_string(value):
  return isinstance(value, str) and value.lower().strip() in YES_STRINGS

def validate_no_string(value):
  return isinstance(value, str) and value.lower().strip() in NO_STRINGS

def string_validator(value, _):
  return isinstance(value, str)

def env_validator(env, valid_envs):
  global AWS_ACCOUNT
  if string_in_list_validator(env, valid_envs):
    check = does_aws_account_match(env)
    if not check:
      print(CRED_STICK_ERROR_MSG)
    return check
  return False

def version_validator(version_string, valid_version_strings):
  version_string = version_string.lower().strip()
  print(version_string)
  if isinstance(valid_version_strings, list) and len(valid_version_strings) > 0:
    if version_string not in valid_version_strings:
      return False
  version_pattern = re.compile(r'^\d+(\.\d+){2}$') # strings like 0.25.1, <int>.<int>.<int>
  if version_pattern.match(version_string):
    return True
  return False

def string_in_list_validator(string, list):
  return isinstance(string, str) and string in list

def directory_validator(path, _):
  return os.path.isdir(path)

def file_exists_validator(str, _ = None):
  files_in_directory = list(map(lambda value: os.path.splitext(value)[0], os.listdir()))
  return str in files_in_directory

def mfa_arn_validator(arn, _ = None):
  pattern = r"arn:aws:iam::\d{1,}:mfa/[a-zA-Z0-9_-]+"
  return isinstance(arn, str) and re.match(re.compile(pattern), arn)

def print_args(args):
  print("🟢 Using CLI args")
  print("args = ", json.dumps(vars(args), indent=2), "\n")

def validate_profile_exists(profile_name):
  config_file_found = False
  credentials_file_found = False
  print(f"Checking for profile {profile_name} in {AWS_CONFIG_FILE_PATH} and {AWS_CREDENTIALS_FILE_PATH}...")
  try:
    with open(AWS_CONFIG_FILE_PATH, "r") as file:
      config_file_found = profile_name in file.read()
    with open(AWS_CREDENTIALS_FILE_PATH, "r") as file:
      credentials_file_found = profile_name in file.read()
    if not config_file_found and not credentials_file_found:
      print(f"❌ Profile {profile_name} not found in {AWS_CONFIG_FILE_PATH} or {AWS_CREDENTIALS_FILE_PATH}")
    return config_file_found and credentials_file_found
  except FileNotFoundError:
    print(f"❌ FileNotFound: {FileNotFoundError}\n")
    return False

def create_profile(profile_name, role_arn):
  mfa_arn = get_aws_mfa_arn()
  AWS_ACCOUNT_ID = get_aws_account_id()
  role_arn = role_arn.format(aws_account=AWS_ACCOUNT_ID)
  print(f"Creating profile {profile_name} with role_arn {role_arn} and mfa_arn {mfa_arn}...\n")
  with open(AWS_CONFIG_FILE_PATH, "a") as file:
    file.write(f"[profile {profile_name}]\n")
    file.write("region = us-west-2\n")
    file.write(f"role_arn = {role_arn}\n")
    file.write("source_profile = default\n\n")
  print(f"✅ Created [profile {profile_name}] in {AWS_CONFIG_FILE_PATH}")
  with open(AWS_CREDENTIALS_FILE_PATH, "a") as file:
    file.write(f"[{profile_name}]\n")
    file.write(f"mfa_serial = {mfa_arn}\n\n")
  print(f"✅ Created [{profile_name}] in {AWS_CREDENTIALS_FILE_PATH}")

def get_aws_mfa_arn():
  print("Fetching MFA devices...")
  iam = boto3.client("iam")
  response = iam.list_mfa_devices()
  for device in response["MFADevices"]:
    if mfa_arn_validator(device["SerialNumber"]):
        print(f"🟢 Found MFA device with ARN {device['SerialNumber']}")
        return device["SerialNumber"]
  print("❌ No MFA devices found")
  return ""

def multi_run(values, process_function):
  results = {}
  for value in values:
    return_code = process_function(value)
    results[value] = return_code
  print_result_codes(results)

def print_result_codes(results):
  def map_code_to_emoji(code):
    return "🟢" if code == 0 else "❌"
  print("\nOverall results:")
  for key, value in results.items():
    print(f" ↪ {map_code_to_emoji(value)} {key}: {value}")
  print("\n")
def exists_makefile(function_name):
  file_path = f"{function_name}/makefile"
  return os.path.exists(file_path)

