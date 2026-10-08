import json
import sys
from pathlib import Path
from docx_records import read_document
from workflow_tools import collect, publish, load_rows, resolve_local

settings = json.loads(Path(__file__).with_name('settings.json').read_text())
if len(sys.argv) == 3 and sys.argv[1] == 'inspect':
    print(json.dumps(read_document(resolve_local(sys.argv[2])), indent=2))
else:
    collect(settings, expand_default=False, retain_default=False)
