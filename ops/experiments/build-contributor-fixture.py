#!/usr/bin/env python3
"""Package only the tested contributor classes, without another copy of SWRLAPI."""
from pathlib import Path
import sys
import zipfile

plugin = Path(sys.argv[1])
output = Path(sys.argv[2])
graphical = '--graphical' in sys.argv[3:]
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
if graphical:
    manifest = manifest.rstrip() + ',\n' + (
        ' org.osgi.framework,javax.swing,javax.swing.event,javax.swing.table,\n'
        ' org.protege.editor.core,org.protege.editor.core.editorkit,\n'
        ' org.protege.editor.core.ui.workspace,org.protege.editor.core.plugin,\n'
        ' org.protege.editor.owl,org.protege.editor.owl.model,\n'
        ' org.protege.editor.owl.ui,org.semanticweb.owlapi.model,\n'
        ' org.swrlapi.ui.model\n'
        'Bundle-Activator: org.swrltab.fixture.GraphicalPluginProbe\n\n'
    )
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as jar:
    jar.writestr('META-INF/MANIFEST.MF', manifest.replace('\n', '\r\n'))
    jar.write(plugin / 'src/test/resources/contributor/plugin.xml', 'plugin.xml')
    jar.write(plugin / 'license.txt', 'META-INF/LICENSE.txt')
    for name in ['ExampleLibrary', 'ExampleLibraryFactory']:
        entry = 'org/swrltab/fixture/' + name + '.class'
        jar.write(plugin / 'target/test-classes' / entry, entry)
    if graphical:
        for compiled in (plugin / 'target/test-classes/org/swrltab/fixture').glob('GraphicalPluginProbe*.class'):
            jar.write(compiled, 'org/swrltab/fixture/' + compiled.name)
print(output)
