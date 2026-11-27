"""Regression guards for accidental cross-version plugin update publication."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).with_name('check-plugin-update-channels.py')
SPEC = importlib.util.spec_from_file_location('channels', SCRIPT)
CHANNELS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHANNELS)
PLUGIN = SCRIPT.resolve().parents[2] / 'swrltab-plugin'


class PluginUpdateChannelsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='swrl-update-channels-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copy2(PLUGIN / 'pom.xml', self.root / 'pom.xml')
        shutil.copytree(PLUGIN / 'update-info', self.root / 'update-info')

    def change(self, path, before, after):
        target = self.root / path
        text = target.read_text()
        self.assertIn(before, text)
        target.write_text(text.replace(before, after))

    def test_current_channels_are_separate(self):
        CHANNELS.check(self.root)

    def test_legacy_feed_cannot_be_advanced_to_the_new_plugin(self):
        self.change('update-info/protege-5/update.properties', '2.1.4', '2.1.5')
        with self.assertRaisesRegex(ValueError, 'version'):
            CHANNELS.check(self.root)

    def test_legacy_download_cannot_point_to_new_plugin(self):
        self.change('update-info/protege-5/update.properties', 'release-2.1.4/swrltab-plugin-2.1.4.jar',
                    'release-2.1.5/swrltab-plugin-2.1.5.jar')
        with self.assertRaisesRegex(ValueError, 'Download'):
            CHANNELS.check(self.root)

    def test_legacy_readme_cannot_follow_master(self):
        self.change('update-info/protege-5/update.properties', '/release-2.1.4/src/', '/master/src/')
        with self.assertRaisesRegex(ValueError, 'Readme'):
            CHANNELS.check(self.root)

    def test_new_feed_must_warn_about_host_version(self):
        self.change('update-info/protege-6/update.properties.template', ' (Protege 6 only)', '')
        with self.assertRaisesRegex(ValueError, 'label'):
            CHANNELS.check(self.root)

    def test_rendered_release_is_allowed_but_snapshot_is_not(self):
        template = (self.root / 'update-info/protege-6/update.properties.template').read_text()
        rendered = self.root / 'update-info/protege-6/update.properties'
        rendered.write_text(template.replace('@VERSION@', '2.1.5'))
        CHANNELS.check(self.root)
        rendered.write_text(template.replace('@VERSION@', '2.1.5-SNAPSHOT'))
        with self.assertRaisesRegex(ValueError, 'released version'):
            CHANNELS.check(self.root)

    def test_pom_cannot_accept_protege_five(self):
        self.change('pom.xml', '[6.0.0,7.0.0)', '[5.0.0,7.0.0)')
        with self.assertRaisesRegex(ValueError, 'exclude Protégé 5'):
            CHANNELS.check(self.root)

    def test_host_import_cannot_be_optional(self):
        self.change('pom.xml', 'org.protege.editor.core.*;', 'org.protege.editor.core.*;resolution:=optional;')
        with self.assertRaisesRegex(ValueError, 'mandatory'):
            CHANNELS.check(self.root)

    def test_packaged_manifest_must_keep_the_same_barrier(self):
        for version, valid in [('[6.0.0,7.0.0)', True), ('[5.0.0,7.0.0)', False)]:
            with self.subTest(version=version):
                jar = self.root / 'plugin.jar'
                with zipfile.ZipFile(jar, 'w') as archive:
                    archive.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\r\n'
                        'Bundle-SymbolicName: swrltab-plugin;singleton:=true\r\n'
                        f'Import-Package: org.protege.editor.core;version="{version}",\r\n'
                        f' org.protege.editor.owl;version="{version}"\r\n\r\n')
                if valid:
                    CHANNELS.check(self.root, jar)
                else:
                    with self.assertRaisesRegex(ValueError, 'exclude Protégé 5'):
                        CHANNELS.check(self.root, jar)


if __name__ == '__main__':
    unittest.main()
