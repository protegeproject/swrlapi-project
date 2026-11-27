#!/usr/bin/env python3
"""Run the opt-in Swing regression fixture in a fresh copy of the built host."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('distribution', type=Path)
parser.add_argument('plugin', type=Path)
parser.add_argument('fixture', type=Path)
parser.add_argument('ontology', type=Path)
parser.add_argument('--java-home', type=Path, required=True)
parser.add_argument('--keep-open', action='store_true')
args = parser.parse_args()
root = Path(tempfile.mkdtemp(prefix='swrlapi-graphical-'))
app = root / 'application'
shutil.copytree(args.distribution, app)
(app / 'plugins').mkdir(exist_ok=True)
for path in (args.plugin, args.fixture):
    shutil.copy2(path, app / 'plugins' / path.name)
    print(path.name, hashlib.sha256(path.read_bytes()).hexdigest(), flush=True)
shutil.copy2(args.ontology, root / 'smoke.owl')
result = root / 'result.txt'
(app / 'conf/jvm.conf').write_text(
    f'max_heap_size=2G\njava_home={args.java_home}\n'
    f'append=-Duser.home={root / "user"} -Dswrlapi.guiSmoke={result} '
    f'-Dswrlapi.guiSmoke.closeEditor={str(not args.keep_open).lower()}\n')
print('Evidence directory:', root, flush=True)
with (root / 'launch.log').open('w') as log:
    process = subprocess.Popen(['./run.sh', str(root / 'smoke.owl')], cwd=app,
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    passed = False
    try:
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and process.poll() is None:
            if result.exists():
                evidence = result.read_text()
                print(evidence, flush=True)
                if not evidence.endswith('GRAPHICAL PLUGIN PASS\n'):
                    raise SystemExit('Graphical regression failed; see ' + str(root))
                passed = True
                break
            time.sleep(0.5)
        if not passed:
            raise SystemExit('No graphical PASS within 120 seconds; see ' + str(root))
    finally:
        if not (passed and args.keep_open):
            try:
                os.killpg(process.pid, 15)
            except ProcessLookupError:
                pass
            process.wait(timeout=15)
        else:
            print('Test process group:', process.pid, flush=True)
