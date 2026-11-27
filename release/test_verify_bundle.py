"""Check release payload selection and validation; mock only external GPG verification."""
import contextlib
import hashlib
import io
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).with_name('verify-bundle.py')
VERSION = '2.1.5'


class VerifyBundleTest(unittest.TestCase):
    def verify(self, *, missing_zip=False, bad_zip_checksum=False, bad_parent_version=False):
        with tempfile.TemporaryDirectory(prefix='swrl-bundle-metadata-') as directory:
            bundle = Path(directory) / 'bundle.zip'
            with zipfile.ZipFile(bundle, 'w') as archive:
                for artifact in ['swrlapi-parent', 'swrlapi', 'swrlapi-drools-engine', 'swrltab-plugin', 'swrltab']:
                    prefix = f'edu/stanford/swrl/{artifact}/{VERSION}/{artifact}-{VERSION}'
                    version = '9.9.9' if bad_parent_version and artifact == 'swrltab' else VERSION
                    parent = (f'<version>{version}</version>' if artifact == 'swrlapi-parent' else
                              '<parent><groupId>edu.stanford.swrl</groupId><artifactId>swrlapi-parent</artifactId>'
                              f'<version>{version}</version></parent>')
                    pom = (f'<project xmlns="http://maven.apache.org/POM/4.0.0">{parent}'
                           f'<artifactId>{artifact}</artifactId><scm><tag>release-{VERSION}</tag></scm></project>')
                    payloads = {'.pom': pom.encode()}
                    if artifact != 'swrlapi-parent':
                        payloads.update({suffix: b'fixture jar' for suffix in ['.jar', '-sources.jar', '-javadoc.jar']})
                    if artifact == 'swrltab' and not missing_zip:
                        payloads['-application.zip'] = b'fixture application archive'
                    for suffix, payload in payloads.items():
                        name = prefix + suffix
                        archive.writestr(name, payload)
                        archive.writestr(name + '.asc', b'fixture signature verified by the GPG mock')
                        for algorithm in ['md5', 'sha1', 'sha256', 'sha512']:
                            checksum = hashlib.new(algorithm, payload).hexdigest()
                            if bad_zip_checksum and suffix == '-application.zip' and algorithm == 'sha256':
                                checksum = '0' * 64
                            archive.writestr(name + '.' + algorithm, checksum)
            with patch.object(sys, 'argv', [str(SCRIPT), str(bundle), VERSION]), \
                    patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as gpg, \
                    contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(SCRIPT), run_name='__main__')
            return gpg.call_count

    def test_inherited_versions_and_application_zip_are_verified(self):
        self.assertEqual(self.verify(), 18)

    def test_application_distribution_is_required(self):
        with self.assertRaisesRegex(AssertionError, 'Missing standalone application distribution'):
            self.verify(missing_zip=True)

    def test_application_checksum_is_checked(self):
        with self.assertRaisesRegex(AssertionError, 'application.zip'):
            self.verify(bad_zip_checksum=True)

    def test_wrong_inherited_version_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'swrltab-2.1.5.pom'):
            self.verify(bad_parent_version=True)


if __name__ == '__main__':
    unittest.main()
