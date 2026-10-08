import json

def inspect(path):
    return json.loads(path.read_text())
