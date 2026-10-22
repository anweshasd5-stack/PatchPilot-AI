"""Intentionally vulnerable demo input. Never use this in production."""
import subprocess


def lookup_host(host: str):
    # Unsafe: shell command contains a value that may be user-controlled.
    return subprocess.run("ping -c 1 " + host, shell=True, capture_output=True, text=True)


user_expression = "2 + 2"
print(eval(user_expression))  # Unsafe dynamic evaluation for demonstration.
