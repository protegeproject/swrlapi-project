#!/usr/bin/env python3
"""Verify the unmodified Protégé alpha-1 dependency baseline, not security status."""
import argparse
import io
from pathlib import Path
import zipfile


def manifest(jar):
    text = jar.read('META-INF/MANIFEST.MF').decode().replace('\r\n ', '').replace('\n ', '')
    return dict(line.split(': ', 1) for line in text.splitlines() if ': ' in line)


def verify(distribution):
    bundles = {}
    for path in sorted((distribution / 'bundles').glob('*.jar')):
        with zipfile.ZipFile(path) as jar:
            values = manifest(jar)
            name = values.get('Bundle-SymbolicName', '').split(';')[0]
            if not name:
                continue
            if name in bundles:
                raise AssertionError(f'Duplicate bundle {name}: {bundles[name][0]} and {path}')
            bundles[name] = (path, values)
    assert len(bundles) >= 10, 'Incomplete distribution'
    assert bundles['com.google.guava'][1]['Bundle-Version'] == '18.0.0', 'Unexpected host Guava version'
    assert 'com.google.guava.failureaccess' not in bundles, 'Unexpected newer Guava dependency'
    owl_path, owl_manifest = bundles['org.semanticweb.owl.owlapi']
    assert owl_manifest['Bundle-Version'] == '5.5.1', 'Unexpected host OWLAPI version'
    expected = {'lib/jackson-annotations-2.16.1.jar': '2.16.1',
                'lib/jackson-core-2.16.1.jar': '2.16.1',
                'lib/jackson-databind-2.16.1.jar': '2.16.1'}
    with zipfile.ZipFile(owl_path) as jar:
        actual = {name for name in jar.namelist() if name.startswith('lib/jackson-') and name.endswith('.jar')}
        assert actual == set(expected), actual
        for name, version in expected.items():
            assert name in owl_manifest['Bundle-ClassPath'].split(','), name
            with zipfile.ZipFile(io.BytesIO(jar.read(name))) as nested:
                assert manifest(nested)['Implementation-Version'] == version, name
        assert not any('httpclient-osgi' in name or 'httpcore-osgi' in name for name in jar.namelist())
    with zipfile.ZipFile(bundles['org.protege.editor.owl'][0]) as jar:
        # Alpha-1 includes a versioned descriptor but does not enable multi-release loading.
        assert 'module-info.class' not in jar.namelist(), 'Unexpected root JPMS descriptor'
        assert manifest(jar).get('Multi-Release', '').lower() != 'true', 'Unexpected multi-release host bundle'
    print('PASS: original alpha-1 baseline; unique host bundles; Guava 18.0; OWLAPI 5.5.1; embedded Jackson 2.16.1')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('distribution', type=Path)
    verify(parser.parse_args().distribution)
