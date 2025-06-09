import os
import subprocess

def run_aws_command(aws_access_key, aws_secret_key, aws_region, command):
    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = aws_access_key
    env["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
    env["AWS_DEFAULT_REGION"] = aws_region

    result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
    return result.stdout, result.stderr

