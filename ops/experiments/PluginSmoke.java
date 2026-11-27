import org.apache.felix.framework.FrameworkFactory;
import org.osgi.framework.Bundle;
import org.osgi.framework.Constants;
import org.osgi.framework.launch.Framework;

import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.jar.JarFile;

/** Runs the packaged plugin in an isolated Felix framework with the built host bundles. */
public class PluginSmoke {
  public static void main(String[] args) throws Exception {
    if (args.length < 2 || args.length > 3)
      throw new IllegalArgumentException("Usage: PluginSmoke <Protege directory> <plugin jar> [UI fixture output]");
    assertBundleContents(Path.of(args[1]));
    System.setProperty("java.awt.headless", "true");
    Path storage = Files.createTempDirectory("swrlapi-osgi-");
    Map<String, String> config = new HashMap<>();
    config.put(Constants.FRAMEWORK_STORAGE, storage.toString());
    config.put(Constants.FRAMEWORK_STORAGE_CLEAN, Constants.FRAMEWORK_STORAGE_CLEAN_ONFIRSTINIT);
    config.put(Constants.FRAMEWORK_BOOTDELEGATION, "sun.*,com.sun.*,javax.xml.*");
    config.put(Constants.FRAMEWORK_SYSTEMPACKAGES_EXTRA,
      "javax.xml.parsers,org.xml.sax,org.xml.sax.ext,org.xml.sax.helpers");
    Framework framework = new FrameworkFactory().newFramework(config);
    ClassLoader originalLoader = Thread.currentThread().getContextClassLoader();
    try {
      framework.start();
      int installed = 0;
      try (var files = Files.list(Path.of(args[0], "bundles"))) {
        for (Path path : (Iterable<Path>)files.sorted()::iterator) {
          if (!path.toString().endsWith(".jar") || path.getFileName().toString().equals("org.apache.felix.main.jar"))
            continue;
          try (JarFile jar = new JarFile(path.toFile())) {
            if (jar.getManifest() == null || jar.getManifest().getMainAttributes().getValue(Constants.BUNDLE_SYMBOLICNAME) == null)
              continue;
          }
          framework.getBundleContext().installBundle(path.toUri().toString());
          installed++;
        }
      }
      if (installed < 10)
        throw new AssertionError("Incomplete host distribution: " + installed + " bundles");
      Bundle plugin = framework.getBundleContext().installBundle(Path.of(args[1]).toUri().toString());
      System.out.println("Plugin artifact: " + Path.of(args[1]).toRealPath());
      try {
        plugin.start();
      } catch (org.osgi.framework.BundleException failure) {
        for (Bundle dependency : framework.getBundleContext().getBundles()) {
          if ("org.semanticweb.owl.owlapi".equals(dependency.getSymbolicName())
            || "com.google.guava".equals(dependency.getSymbolicName())) {
            try { dependency.start(); }
            catch (org.osgi.framework.BundleException cause) { System.err.println(cause.getMessage()); }
          }
        }
        throw failure;
      }
      if (plugin.getState() != Bundle.ACTIVE)
        throw new AssertionError("Plugin is not ACTIVE");
      System.out.println("Resolved and started " + plugin.getSymbolicName() + " " + plugin.getVersion());
      plugin.loadClass("org.swrltab.ui.SWRLTab");
      plugin.loadClass("org.swrltab.ui.SQWRLTab");
      Class<?> factory = plugin.loadClass("org.swrlapi.factory.SWRLAPIFactory");
      Thread.currentThread().setContextClassLoader(factory.getClassLoader());
      Class<?> owlManager = plugin.loadClass("org.semanticweb.owlapi.apibinding.OWLManager");
      Object manager = owlManager.getMethod("createOWLOntologyManager").invoke(null);
      String turtle = "@prefix : <urn:swrlapi:smoke#> . "
        + "@prefix owl: <http://www.w3.org/2002/07/owl#> . "
        + "<urn:swrlapi:smoke> a owl:Ontology . :Person a owl:Class . :Adult a owl:Class . "
        + ":alice a owl:NamedIndividual, :Person .";
      Object ontology = call(manager, "loadOntologyFromOntologyDocument", new Class<?>[]{InputStream.class},
        new ByteArrayInputStream(turtle.getBytes(StandardCharsets.UTF_8)));
      Object resolver = factory.getMethod("createIRIResolver", String.class).invoke(null, "urn:swrlapi:smoke#");
      Object engine = factory.getMethod("createSQWRLQueryEngine",
        plugin.loadClass("org.semanticweb.owlapi.model.OWLOntology"),
        plugin.loadClass("org.swrlapi.core.IRIResolver")).invoke(null, ontology, resolver);
      Object result = call(engine, "runSQWRLQuery", new Class<?>[]{String.class, String.class},
        "osgiSmoke", "swrlb:add(?sum, 2, 3) -> sqwrl:select(?sum)");
      if (!Integer.valueOf(1).equals(call(result, "getNumberOfRows", new Class<?>[0])))
        throw new AssertionError("Expected exactly one query result");
      if (!Boolean.TRUE.equals(call(result, "next", new Class<?>[0])))
        throw new AssertionError("Missing result row");
      Object literal = call(result, "getLiteral", new Class<?>[]{int.class}, 0);
      if (!BigInteger.valueOf(5).equals(call(literal, "getInteger", new Class<?>[0])))
        throw new AssertionError("Wrong query value");
      if (!Boolean.FALSE.equals(call(result, "next", new Class<?>[0])))
        throw new AssertionError("Unexpected extra result row");
      Object before = call(engine, "runSQWRLQuery", new Class<?>[]{String.class, String.class},
        "before", "Adult(?p) -> sqwrl:select(?p)");
      if (!Integer.valueOf(0).equals(call(before, "getNumberOfRows", new Class<?>[0])))
        throw new AssertionError("Adult must not be inferred before adding the rule");
      Object people = call(engine, "runSQWRLQuery", new Class<?>[]{String.class, String.class},
        "people", "Person(?p) -> sqwrl:select(?p)");
      if (!Integer.valueOf(1).equals(call(people, "getNumberOfRows", new Class<?>[0])))
        throw new AssertionError("Missing asserted Person control");
      call(engine, "createSWRLRule", new Class<?>[]{String.class, String.class},
        "personToAdult", "Person(?p) -> Adult(?p)");
      assertRuleRendering(plugin, ontology);
      if (args.length == 3) {
        Class<?> iri = plugin.loadClass("org.semanticweb.owlapi.model.IRI");
        Object destination = iri.getMethod("create", String.class).invoke(null, Path.of(args[2]).toUri().toString());
        call(manager, "saveOntology", new Class<?>[]{plugin.loadClass("org.semanticweb.owlapi.model.OWLOntology"), iri},
          ontology, destination);
      }
      call(engine, "infer", new Class<?>[0]);
      Object after = call(engine, "runSQWRLQuery", new Class<?>[]{String.class, String.class},
        "after", "Adult(?p) -> sqwrl:select(?p)");
      if (!Integer.valueOf(1).equals(call(after, "getNumberOfRows", new Class<?>[0]))
        || !Boolean.TRUE.equals(call(after, "next", new Class<?>[0])))
        throw new AssertionError("Rule did not infer exactly one Adult");
      Object individual = call(after, "getNamedIndividual", new Class<?>[]{int.class}, 0);
      if (!"urn:swrlapi:smoke#alice".equals(call(individual, "getIRI", new Class<?>[0]).toString()))
        throw new AssertionError("Rule inferred the wrong individual");
      System.out.println("PASS: packaged SWRLTab resolves; both tab classes load; rule rendering preserves prefixes and variables; SQWRL 2 + 3 = 5; rule infers Adult(alice)");
    } finally {
      Thread.currentThread().setContextClassLoader(originalLoader);
      framework.stop();
      framework.waitForStop(10000);
      // Keep isolated framework storage available for diagnosis; it never uses ~/.Protege.
      System.out.println("Felix diagnostics: " + storage);
    }
  }

  private static void assertBundleContents(Path plugin) throws Exception {
    int engineJars = 0;
    try (JarFile jar = new JarFile(plugin.toFile())) {
      var entries = jar.entries();
      while (entries.hasMoreElements()) {
        String name = entries.nextElement().getName();
        if (name.matches("(?:checker|jdk8|junit|slf4j-log4j12|slf4j-simple|owlapi-osgidistribution|protege-editor-owl)-[0-9].*\\.jar"))
          throw new AssertionError("Unwanted compiler, test, or host dependency embedded: " + name);
        if (name.matches("swrlapi(?:-drools-engine)?-[0-9].*\\.jar")) engineJars++;
      }
    }
    if (engineJars != 2) throw new AssertionError("Missing embedded SWRLAPI/engine jars");
  }

  private static void assertRuleRendering(Bundle plugin, Object ontology) throws Exception {
    Class<?> finderType = plugin.loadClass("org.protege.editor.owl.model.find.OWLEntityFinder");
    Class<?> entityType = plugin.loadClass("org.protege.editor.owl.ui.renderer.OWLModelManagerEntityRenderer");
    Class<?> modelType = plugin.loadClass("org.protege.editor.owl.model.OWLModelManager");
    Class<?> objectType = plugin.loadClass("org.protege.editor.owl.ui.renderer.OWLObjectRenderer");
    Class<?> iriType = plugin.loadClass("org.semanticweb.owlapi.model.IRI");
    ClassLoader loader = entityType.getClassLoader();
    Object entities = Proxy.newProxyInstance(loader, new Class<?>[]{entityType}, (proxy, method, args) -> {
      if (method.getName().equals("render") || method.getName().equals("getShortForm")) {
        Object iri = iriType.isInstance(args[0]) ? args[0] : call(args[0], "getIRI", new Class<?>[0]);
        String name = call(iri, "getShortForm", new Class<?>[0]).toString();
        return iri.toString().startsWith("urn:swrlapi:smoke#") ? ":" + name : name;
      }
      throw new AssertionError("Unexpected entity renderer call: " + method);
    });
    Object model = Proxy.newProxyInstance(loader, new Class<?>[]{modelType}, (proxy, method, args) -> {
      if (method.getName().equals("getOWLEntityRenderer")) return entities;
      if (method.getName().equals("getRendering"))
        return entityType.getMethod("render", plugin.loadClass("org.semanticweb.owlapi.model.OWLEntity"))
          .invoke(entities, args[0]);
      throw new AssertionError("Unexpected model manager call: " + method);
    });
    Object finder = Proxy.newProxyInstance(loader, new Class<?>[]{finderType}, (proxy, method, args) -> {
      throw new AssertionError("Rendering must not look up entities: " + method);
    });
    Object hostRenderer = plugin.loadClass("org.protege.editor.owl.ui.renderer.OWLObjectRendererImpl")
      .getConstructor(modelType).newInstance(model);
    Object resolver = plugin.loadClass("org.swrltab.core.ProtegeIRIResolver")
      .getConstructor(finderType, entityType, objectType).newInstance(finder, entities, hostRenderer);
    call(resolver, "updatePrefixes", new Class<?>[]{plugin.loadClass("org.semanticweb.owlapi.model.OWLOntology")}, ontology);
    int matches = 0;
    for (Object axiom : (Iterable<?>)call(ontology, "getAxioms", new Class<?>[0])) {
      String rendering = call(resolver, "render", new Class<?>[]{plugin.loadClass("org.semanticweb.owlapi.model.OWLObject")}, axiom).toString();
      if (rendering.equals("swrlb:add(?sum, 2, 3) -> sqwrl:select(?sum)")) matches++;
    }
    if (matches != 1) throw new AssertionError("Expected exactly one correctly rendered arithmetic query, got " + matches);
  }

  private static Object call(Object object, String name, Class<?>[] types, Object... values) throws Exception {
    Method method = object.getClass().getMethod(name, types);
    method.setAccessible(true);
    return method.invoke(object, values);
  }
}
