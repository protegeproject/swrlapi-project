#!/usr/bin/env python3
"""Upload a signed bundle, inspect a deployment, or publish a validated deployment.
Reads the 'central' token from ~/.m2/settings.xml; never logs credentials.
Uploads are USER_MANAGED. A separate publish command is required.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET

BASE = 'https://central.sonatype.com/api/v1/publisher'

def token():
    root = ET.parse(Path.home()/'.m2/settings.xml').getroot()
    def local(e): return e.tag.rsplit('}', 1)[-1]
    servers = [{local(c): (c.text or '').strip() for c in e} for e in root.iter() if local(e)=='server']
    entries = [s for s in servers if s.get('id')=='central']
    if len(entries)!=1: raise SystemExit('Expected one central server in Maven settings')
    def value(name):
        text=entries[0].get(name, '')
        match=re.fullmatch(r'\$\{env\.([^}]+)\}',text)
        if match: text=os.environ.get(match[1], '')
        if not text or text.startswith('{'): raise SystemExit('Use Portal token credentials or env references; encrypted Maven credentials require the Maven plugin')
        return text
    return base64.b64encode((value('username')+':'+value('password')).encode()).decode()

def request(path, data=b'', content_type=None):
    headers={'Authorization':'Bearer '+token()}
    if content_type: headers['Content-Type']=content_type
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=120) as response: return response.read().decode()
    except urllib.error.HTTPError as error:
        # Do not print request headers or credential-bearing diagnostics.
        raise SystemExit(f'Portal returned HTTP {error.code}; check token, namespace access, or deployment state')

parser=argparse.ArgumentParser(description=__doc__)
sub=parser.add_subparsers(dest='action',required=True)
u=sub.add_parser('upload');u.add_argument('bundle',type=Path);u.add_argument('--name',required=True);u.add_argument('--receipt',type=Path,required=True)
for name in ['status','publish']:
    p=sub.add_parser(name);p.add_argument('deployment_id',type=uuid.UUID)
a=parser.parse_args()
if a.action=='upload':
    if a.receipt.exists(): raise SystemExit('Receipt already exists; inspect it before uploading again')
    boundary='swrlapi-'+uuid.uuid4().hex
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="bundle"; filename="central-bundle.zip"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+a.bundle.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
    result=request('/upload?'+urllib.parse.urlencode({'name':a.name,'publishingType':'USER_MANAGED'}),body,'multipart/form-data; boundary='+boundary).strip()
    uuid.UUID(result)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps({'deploymentId':result,'name':a.name,'bundle':str(a.bundle.resolve())},indent=2)+'\n')
    print('Deployment:',result)
else:
    identifier=str(a.deployment_id)
    state=json.loads(request('/status?'+urllib.parse.urlencode({'id':identifier})))
    if a.action=='status': print(json.dumps(state,indent=2))
    else:
        if state.get('deploymentState')!='VALIDATED': raise SystemExit('Publish requires VALIDATED; current state: '+str(state.get('deploymentState')))
        request('/deployment/'+identifier)
        print('Publication requested:',identifier)
