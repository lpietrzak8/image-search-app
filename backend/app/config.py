import os

def get_secret(name):
    file_var = os.getenv(f"{name}_FILE")
    if file_var and os.path.exists(file_var):
        with open(file_var, 'r') as pw_file:
            return pw_file.read().strip()
    return os.getenv(name)