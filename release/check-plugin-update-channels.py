#!/usr/bin/env python3
"""Keep the Protégé 5 update channel separate from the Protégé 6 plugin."""
import argparse
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

LEGACY_VERSION = '2.1.4'
REPOSITORY = 'https://github.com/protegeproject/swrltab-plugin'
RAW = 'https://raw.githubusercontent.com/protegeproject/swrltab-plugin'
HOST_RANGE = '[6.0.0,7.0.0)'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def properties(path):
    result = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith(('#', '!')):
            key, value = line.split('=', 1)
            require(key.strip() not in result, 'Duplicate update property: ' + key)
            result[key.strip()] = value.strip()
    return result


def check_feed(info, version, label):
    require(info.get('id') == 'swrltab-plugin', 'Wrong plugin identity')
    require(info.get('name') == label, 'Update label must identify its supported host')
    require(info.get('version') == version, 'Unexpected update version')
    require(info.get('download') == f'{REPOSITORY}/releases/download/release-{version}/swrltab-plugin-{version}.jar',
            'Download must identify the expected immutable release')
    require(info.get('readme') == f'{RAW}/release-{version}/src/main/resources/readme.html',
            'Readme must identify the same immutable release')


def check_imports(imports):
    families = set()
    for clause in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', imports):
        name = clause.split(';', 1)[0].strip()
        family = next((p for p in ('org.protege.editor.core', 'org.protege.editor.owl')
                       if name == p or name.startswith(p + '.')), None)
        if family:
            families.add(family)
            version = re.search(r';\s*version\s*=\s*"([^"]+)"', clause)
            require(version is not None and version[1] == HOST_RANGE,
                    'Host import must exclude Protégé 5: ' + name)
            require(not re.search(r'resolution\s*:=\s*"?optional', clause),
                    'Host imports must be mandatory: ' + name)
    require(len(families) == 2, 'Both Protégé core and OWL imports must be present')


def check(root, bundle=None):
    check_feed(properties(root / 'update-info/protege-5/update.properties'), LEGACY_VERSION, 'SWRLTab')
    check_feed(properties(root / 'update-info/protege-6/update.properties.template'), '@VERSION@',
               'SWRLTab (Protege 6 only)')
    rendered = root / 'update-info/protege-6/update.properties'
    if rendered.exists():
        info = properties(rendered)
        version = info.get('version', '')
        require(re.fullmatch(r'\d+\.\d+\.\d+', version) is not None,
                'Only a released version may appear in the Protégé 6 feed')
        check_feed(info, version, 'SWRLTab (Protege 6 only)')
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    imports = ET.parse(root / 'pom.xml').findtext('.//m:Import-Package', namespaces=ns)
    require(imports is not None, 'Missing host imports in plugin POM')
    check_imports(imports)
    if bundle is not None:
        with zipfile.ZipFile(bundle) as jar:
            manifest = jar.read('META-INF/MANIFEST.MF').decode().replace('\r\n', '\n').replace('\n ', '')
        headers = dict(line.split(': ', 1) for line in manifest.split('\n\n', 1)[0].splitlines() if ': ' in line)
        require(headers.get('Bundle-SymbolicName', '').split(';')[0] == 'swrltab-plugin', 'Wrong bundle identity')
        check_imports(headers.get('Import-Package', ''))
        require('/protege-5/' not in headers.get('Update-Url', ''), 'Protégé 6 bundle must not use the legacy feed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plugin', type=Path)
    parser.add_argument('--bundle', type=Path)
    args = parser.parse_args()
    check(args.plugin, args.bundle)
    print('PASS: frozen Protégé 5 feed, separate labelled Protégé 6 feed, mandatory host version range')
