import os
import subprocess

for file in os.listdir("."):
    if file.endswith(".proto"):
        print(file)
        subprocess.run(["protoc", "--python_out=.", file] )