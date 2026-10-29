#!/usr/bin/env python3
"""Align sibling SWRL projects for a coordinated release or next development cycle.

Does not build, commit, tag, push, or publish. Review the resulting diffs.
"""
import argparse
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

CORE = {'swrlapi-parent', 'swrlapi', 'swrlapi-drools-engine', 'swrltab-plugin', 'swrltab'}
AUX = {'swrlapi-project', 'swrlapi-example', 'swrlapi-integration-tests', 'swrlapi-builtin-library-example'}
NS = {'m': 'http://maven.apache.org/POM/4.0.0'}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('version', help='e.g. 2.1.4 or 2.1.5-SNAPSHOT')
args = parser.parse_args()
if not re.fullmatch(r'\d+\.\d+\.\d+(?:-SNAPSHOT)?', args.version):
    parser.error('Expected x.y.z or x.y.z-SNAPSHOT')
root = Path(__file__).resolve().parents[2]
changes = []
for name in sorted(CORE | AUX):
    repo = root / name
    branch = subprocess.check_output(['git', '-C', str(repo), 'branch', '--show-current'], text=True).strip()
    if branch != 'development':
        raise SystemExit(f'{name}: expected development, found {branch}')
    pom = repo / 'pom.xml'
    text = pom.read_text()
    tree = ET.fromstring(text)
    old = tree.findtext('m:version', namespaces=NS)
    artifact = tree.findtext('m:artifactId', namespaces=NS)
    # Restrict replacements to SWRL version elements; unrelated plugin versions remain untouched.
    for tag in ['swrlapi.version', 'swrlapi.drools.version']:
        text = re.sub(r'(<'+re.escape(tag)+r'>)[^<]+(</'+re.escape(tag)+r'>)', lambda m:m[1]+args.version+m[2], text)
    text = re.sub(r'(<parent>.*?<groupId>edu.stanford.swrl</groupId>.*?<version>)[^<]+(</version>.*?</parent>)', lambda m:m[1]+args.version+m[2], text, flags=re.S)
    own = args.version if name in CORE or args.version.endswith('-SNAPSHOT') else args.version+'-SNAPSHOT'
    pattern = r'(<artifactId>'+re.escape(artifact)+r'</artifactId>\s*<version>)'+re.escape(old)+r'(</version>)'
    text, count = re.subn(pattern, lambda m:m[1]+own+m[2], text, count=1)
    if count != 1:
        raise SystemExit(f'{name}: cannot uniquely locate project version')
    if name in CORE:
        tag = 'HEAD' if args.version.endswith('-SNAPSHOT') else 'release-'+args.version
        text = re.sub(r'(<scm>.*?<tag>)[^<]+(</tag>.*?</scm>)', lambda m:m[1]+tag+m[2], text, flags=re.S)
    ET.fromstring(text)
    changes.append((pom, text))
for pom, text in changes:
    pom.write_text(text)
    print(pom.parent.name, args.version)
