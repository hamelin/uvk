import os
import sys

print("Python", sys.version)
print("Installed in", sys.base_prefix)
if "VIRTUAL_ENV" in os.environ:
    print("Virtual environment:", os.environ["VIRTUAL_ENV"])
