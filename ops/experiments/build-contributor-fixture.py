#!/usr/bin/env python3
"""Package only the tested contributor classes, without another copy of SWRLAPI."""
from pathlib import Path
import sys
import zipfile

plugin = Path(sys.argv[1])
output = Path(sys.argv[2])
manifest = (
    'Manifest-Version: 1.0\n'
    'Bundle-ManifestVersion: 2\n'
    'Bundle-SymbolicName: swrlapi-contributor-fixture;singleton:=true\n'
    'Bundle-Name: SWRLAPI Contributor Test Fixture\n'
    'Bundle-Version: 1.0.0\n'
    'Import-Package: org.swrltab.core;version="[2.1,3)",\n'
    ' org.swrlapi.builtins;version="[2.1,3)",\n'
    ' org.swrlapi.builtins.arguments;version="[2.1,3)",\n'
    ' org.swrlapi.exceptions;version="[2.1,3)"\n\n'
)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as jar:
    jar.writestr('META-INF/MANIFEST.MF', manifest.replace('\n', '\r\n'))
    jar.write(plugin / 'src/test/resources/contributor/plugin.xml', 'plugin.xml')
    for name in ['ExampleLibrary', 'ExampleLibraryFactory']:
        entry = 'org/swrltab/fixture/' + name + '.class'
        jar.write(plugin / 'target/test-classes' / entry, entry)
print(output)
