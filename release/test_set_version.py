"""Exercise release metadata preparation without touching working checkouts."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).with_name('set-version.py')
WORKSPACE = SCRIPT.resolve().parents[2]
REPOS = ['swrlapi-parent', 'swrlapi', 'swrlapi-drools-engine', 'swrltab-plugin', 'swrltab']
NS = {'m': 'http://maven.apache.org/POM/4.0.0'}


class SetVersionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='swrl-release-metadata-')
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        for name in REPOS:
            repo = self.workspace / name
            repo.mkdir()
            (repo / 'pom.xml').write_bytes((WORKSPACE / name / 'pom.xml').read_bytes())
            subprocess.run(['git', 'init', '-q', '-b', 'protege-6', str(repo)], check=True)

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args, '--workspace', str(self.workspace)],
                              capture_output=True, text=True)

    def test_release_and_next_snapshot_support_inherited_versions_and_missing_optional_modules(self):
        for version, tag in [('2.1.5', 'release-2.1.5'), ('2.1.6-SNAPSHOT', 'HEAD')]:
            result = self.run_script(version, '--branch', 'protege-6')
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in REPOS:
                pom = ET.parse(self.workspace / name / 'pom.xml').getroot()
                effective = pom.findtext('m:version', namespaces=NS) or pom.findtext('m:parent/m:version', namespaces=NS)
                self.assertEqual(effective, version, name)
                self.assertEqual(pom.findtext('m:scm/m:tag', namespaces=NS), tag, name)
                if name != 'swrlapi-parent':
                    self.assertEqual(pom.findtext('m:parent/m:version', namespaces=NS), version, name)

    def test_wrong_branch_rejects_before_writing_any_pom(self):
        before = {name: (self.workspace / name / 'pom.xml').read_bytes() for name in REPOS}
        result = self.run_script('2.1.5')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('expected development, found protege-6', result.stderr)
        for name in REPOS:
            self.assertEqual((self.workspace / name / 'pom.xml').read_bytes(), before[name])


if __name__ == '__main__':
    unittest.main()
