import org.osgi.framework.Version;
import org.protege.editor.core.update.PluginInfo;
import org.protege.editor.core.update.PluginInfoDocumentParser;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.jar.JarFile;

/** Validate release metadata against the built bundle using the host's update parser. */
public class PluginUpdateSmoke {
  public static void main(String[] args) throws Exception {
    if (args.length != 2)
      throw new IllegalArgumentException("Expected update.properties.template and plugin.jar");
    try (JarFile jar = new JarFile(args[1])) {
      var attributes = jar.getManifest().getMainAttributes();
      String id = attributes.getValue("Bundle-SymbolicName").split(";")[0];
      Version bundleVersion = new Version(attributes.getValue("Bundle-Version"));
      String release = bundleVersion.getMajor() + "." + bundleVersion.getMinor() + "." + bundleVersion.getMicro();
      String template = Files.readString(Path.of(args[0]));
      if (!template.contains("@VERSION@")) throw new AssertionError("Missing release placeholder");
      Path rendered = Files.createTempFile("swrl-update-metadata-", ".properties");
      try {
        Files.writeString(rendered, template.replace("@VERSION@", release));
        PluginInfo info = new PluginInfoDocumentParser(rendered.toUri().toURL()).parseDocument(Optional.empty());
        if (!id.equals(info.getId())) throw new AssertionError("Update ID differs from bundle");
        if (!new Version(release).equals(info.getAvailableVersion()))
          throw new AssertionError("Update version differs from bundle's release version");
        String repository = "https://github.com/protegeproject/swrltab-plugin";
        String download = repository + "/releases/download/release-" + release + "/swrltab-plugin-" + release + ".jar";
        if (!download.equals(info.getDownloadURL().toString())) throw new AssertionError("Unexpected download URL");
        String readme = "https://raw.githubusercontent.com/protegeproject/swrltab-plugin/release-" + release
          + "/src/main/resources/readme.html";
        if (!readme.equals(info.getReadmeURI().orElseThrow().toString()))
          throw new AssertionError("Readme must identify the same release tag");
        if (!"SWRLTab".equals(info.getLabel())) throw new AssertionError("Missing plugin label");
        System.out.println("PASS: Protégé update parser accepts release metadata for " + id + " " + release);
        System.out.println("Template validation only; release URLs were not fetched or published.");
      } finally {
        Files.deleteIfExists(rendered);
      }
    }
  }
}
