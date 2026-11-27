#!/usr/bin/env python3
"""Verify strict nullness enforcement and the narrow JDK dependency models."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
from xml.sax.saxutils import escape


def main():
    parent = Path(__file__).resolve().parents[3] / "swrlapi-parent" / "pom.xml"
    with tempfile.TemporaryDirectory(prefix="swrlapi-nullness-probe-") as directory:
        root = Path(directory).resolve()
        (root / "pom.xml").write_text(f"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>edu.stanford.swrl</groupId><artifactId>swrlapi-parent</artifactId>
    <version>2.1.5-SNAPSHOT</version><relativePath>{escape(os.path.relpath(parent, root))}</relativePath>
  </parent>
  <artifactId>nullness-profile-probe</artifactId>
  <dependencies><dependency>
    <groupId>org.checkerframework</groupId><artifactId>checker-qual</artifactId>
  </dependency></dependencies>
</project>
""")
        source = root / "src/main/java/NullnessProbe.java"
        source.parent.mkdir(parents=True)
        for guarded in (True, False):
            expression = "value == null ? 0 : value.length()" if guarded else "value.length()"
            source.write_text("import org.checkerframework.checker.nullness.qual.Nullable;\n"
                              "final class NullnessProbe {\n"
                              "  static int length(@Nullable String value) {\n"
                              f"    return {expression};\n"
                              "  }\n"
                              "  static void allowedNulls(javax.xml.datatype.DatatypeFactory factory,\n"
                              "      javax.xml.crypto.dsig.TransformService transform) throws Exception {\n"
                              "    factory.newDuration(true, null, null, java.math.BigInteger.ONE, null, null, null);\n"
                              "    transform.init((javax.xml.crypto.dsig.spec.TransformParameterSpec)null);\n"
                              "    new javax.swing.JTabbedPane().addTab(null, null, null, null);\n"
                              "  }\n}\n")
            result = subprocess.run(
                ["mvn", "-o", "-B", "-f", str(root / "pom.xml"),
                 "-Pnullness", "-Dchecker.stubs=" + str(parent.parent / "src/main/checker/jdk.astub"),
                 "clean", "compile"],
                env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=120)
            if (result.returncode == 0) != guarded:
                raise AssertionError(f"Unexpected strict checker exit {result.returncode}:\n{result.stdout}")
            findings = set(re.findall(r"NullnessProbe.java:\[\d+,\d+\].*dereference.of.nullable\]", result.stdout))
            expected = 0 if guarded else 1
            if len(findings) != expected:
                raise AssertionError(f"Expected {expected} probe findings:\n{result.stdout}")
            print(f"{'Guarded' if guarded else 'Unsafe'} probe: {len(findings)} expected findings")


if __name__ == "__main__":
    main()
