#!/usr/bin/env python3
"""Check the exact five-artifact release scope, POMs, signatures, and checksums."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('bundle',type=Path)
parser.add_argument('version')
a=parser.parse_args()
expected={'swrlapi-parent','swrlapi','swrlapi-drools-engine','swrltab-plugin','swrltab'}
ns={'m':'http://maven.apache.org/POM/4.0.0'}
with zipfile.ZipFile(a.bundle) as z, tempfile.TemporaryDirectory(prefix='swrl-release-verify-') as temp:
    names=set(z.namelist())
    poms=[n for n in names if n.endswith('.pom')]
    found={}
    for name in poms:
        r=ET.fromstring(z.read(name))
        artifact=r.findtext('m:artifactId',namespaces=ns)
        assert artifact not in found, f'Duplicate POM: {artifact}'
        found[artifact]=name
        assert r.findtext('m:version',namespaces=ns)==a.version, name
        assert r.findtext('m:scm/m:tag',namespaces=ns)=='release-'+a.version, name
        for elem in r.findall('.//m:version',ns):
            assert not (elem.text or '').endswith('-SNAPSHOT'), name+' contains snapshot version'
    assert set(found)==expected, f'Unexpected artifacts: {set(found)}'
    for artifact,name in found.items():
        prefix=f'edu/stanford/swrl/{artifact}/{a.version}/{artifact}-{a.version}'
        assert name==prefix+'.pom',name
        if artifact!='swrlapi-parent':
            for suffix in ['.jar','-sources.jar','-javadoc.jar']:
                assert prefix+suffix in names, f'Missing {prefix+suffix}'
    payloads=[n for n in names if n.endswith(('.pom','.jar'))]
    for i,name in enumerate(sorted(payloads)):
        assert name+'.asc' in names, f'Missing signature for {name}'
        payload=z.read(name)
        for algorithm in ['md5','sha1','sha256','sha512']:
            assert name+'.'+algorithm in names, f'Missing checksum for {name}'
            assert hashlib.new(algorithm,payload).hexdigest()==z.read(name+'.'+algorithm).decode().strip(),name
        data=Path(temp)/str(i); data.write_bytes(payload)
        sig=Path(temp)/(str(i)+'.asc');sig.write_bytes(z.read(name+'.asc'))
        result=subprocess.run(['gpg','--batch','--verify',str(sig),str(data)],capture_output=True,text=True)
        assert result.returncode==0, f'Invalid signature: {name}'
    print(f'Verified {len(found)} artifacts, {len(payloads)} signed files, and all checksums for {a.version}.')
