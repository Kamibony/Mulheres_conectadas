import sys

def read_file(filepath):
    with open(filepath, 'r') as f:
        print(f"--- {filepath} ---")
        print(f.read())
        print(f"--- EOF {filepath} ---\n")

read_file('functions/main.py')
read_file('functions/tests/test_main.py')
read_file('functions/tests/benchmark.py')
