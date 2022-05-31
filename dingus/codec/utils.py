import os
import subprocess


def compile_schemas():
    for file in os.listdir("."):
        if file.endswith(".proto"):
            print(file)
            subprocess.run(["protoc", "--python_out=.", file], stdout=subprocess.PIPE)
