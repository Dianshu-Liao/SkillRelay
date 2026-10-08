import json
import sys
from pathlib import Path
from workflow_tools import collect, publish, load_rows, resolve_local

settings = json.loads(Path(__file__).with_name('settings.json').read_text())
if len(sys.argv) == 3 and sys.argv[1] == 'inspect':
    state = resolve_local(sys.argv[2])
    companion = state.with_suffix(".handoff.txt")
    print(json.dumps({"records": load_rows(state), "editorial_handoff": companion.read_text() if companion.exists() else ""}, indent=2))
else:
    collect(settings, expand_default=False, retain_default=False)
