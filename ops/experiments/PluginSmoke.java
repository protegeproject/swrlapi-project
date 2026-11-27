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
    if (args.length < 2 || args.length > 4)
      throw new IllegalArgumentException("Usage: PluginSmoke <Protege directory> <plugin jar> [UI fixture output] [contributor jar]");
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
      Map<String, Path> symbolicNames = new HashMap<>();
      try (var files = Files.list(Path.of(args[0], "bundles"))) {
        for (Path path : (Iterable<Path>)files.sorted()::iterator) {
          if (!path.toString().endsWith(".jar") || path.getFileName().toString().equals("org.apache.felix.main.jar"))
            continue;
          try (JarFile jar = new JarFile(path.toFile())) {
            if (jar.getManifest() == null || jar.getManifest().getMainAttributes().getValue(Constants.BUNDLE_SYMBOLICNAME) == null)
              continue;
            String name = jar.getManifest().getMainAttributes().getValue(Constants.BUNDLE_SYMBOLICNAME).split(";")[0];
            Path previous = symbolicNames.putIfAbsent(name, path);
            if (previous != null)
              throw new AssertionError("Duplicate host bundle " + name + ": " + previous + " and " + path);
          }
          framework.getBundleContext().installBundle(path.toUri().toString());
          installed++;
        }
      }
      if (installed < 10)
        throw new AssertionError("Incomplete host distribution: " + installed + " bundles");
      Bundle owlBundle = java.util.Arrays.stream(framework.getBundleContext().getBundles())
        .filter(bundle -> "org.semanticweb.owl.owlapi".equals(bundle.getSymbolicName()))
        .findFirst().orElseThrow(() -> new AssertionError("Missing OWLAPI bundle"));
      owlBundle.start();
      Bundle guavaBundle = java.util.Arrays.stream(framework.getBundleContext().getBundles())
        .filter(bundle -> "com.google.guava".equals(bundle.getSymbolicName()))
        .findFirst().orElseThrow(() -> new AssertionError("Missing Guava bundle"));
      guavaBundle.start();
      System.out.println("Host OWLAPI: " + owlBundle.getVersion() + " from " + owlBundle.getLocation());
      System.out.println("Host Guava: " + guavaBundle.getVersion() + " from " + guavaBundle.getLocation());
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
      startRegistry(framework, plugin);
      Object loader = plugin.loadClass("org.swrltab.core.SWRLBuiltInLibraryFactoryLoader").getConstructor().newInstance();
      if (!((java.util.Set<?>)call(loader, "getPlugins", new Class<?>[0])).isEmpty())
        throw new AssertionError("Expected no contributed libraries before installing fixture");
      if (args.length == 4) {
        Bundle contributor = framework.getBundleContext().installBundle(Path.of(args[3]).toUri().toString());
        contributor.start();
        if (contributor.getState() != Bundle.ACTIVE)
          throw new AssertionError("Contributor is not ACTIVE");
        if (contributor.loadClass("org.swrlapi.builtins.SWRLBuiltInLibrary")
          != plugin.loadClass("org.swrlapi.builtins.SWRLBuiltInLibrary"))
          throw new AssertionError("Contributor and engine have different library API classes");
        if (((java.util.Set<?>)call(loader, "getPlugins", new Class<?>[0])).size() != 1)
          throw new AssertionError("Expected exactly one registered contribution");
      }
      Class<?> factory = plugin.loadClass("org.swrlapi.factory.SWRLAPIFactory");
      Thread.currentThread().setContextClassLoader(factory.getClassLoader());
      Class<?> owlManager = plugin.loadClass("org.semanticweb.owlapi.apibinding.OWLManager");
      Object manager = owlManager.getMethod("createOWLOntologyManager").invoke(null);
      String turtle = "@prefix : <urn:swrlapi:smoke#> . "
        + "@prefix owl: <http://www.w3.org/2002/07/owl#> . "
        + "<urn:swrlapi:smoke> a owl:Ontology . :Person a owl:Class . :Adult a owl:Class . :ContributedAdult a owl:Class . "
        + ":alice a owl:NamedIndividual, :Person .";
      Object ontology = call(manager, "loadOntologyFromOntologyDocument", new Class<?>[]{InputStream.class},
        new ByteArrayInputStream(turtle.getBytes(StandardCharsets.UTF_8)));
      Object resolver = factory.getMethod("createIRIResolver", String.class).invoke(null, "urn:swrlapi:smoke#");
      Object owner = plugin.loadClass("org.swrltab.core.SWRLTabEngineFactory").getConstructor().newInstance();
      Object engine = call(owner, "createSQWRLQueryEngine", new Class<?>[]{
        plugin.loadClass("org.semanticweb.owlapi.model.OWLOntology"),
        plugin.loadClass("org.swrlapi.core.IRIResolver")}, ontology, resolver);
      if (args.length == 4) {
        Object answer = call(engine, "runSQWRLQuery", new Class<?>[]{String.class, String.class},
          "contributedAnswer", "contributed:answer(?value) -> sqwrl:select(?value)");
        if (!Integer.valueOf(1).equals(call(answer, "getNumberOfRows", new Class<?>[0]))
          || !Boolean.TRUE.equals(call(answer, "next", new Class<?>[0])))
          throw new AssertionError("Contributed query did not return exactly one row");
        Object value = call(answer, "getLiteral", new Class<?>[]{int.class}, 0);
        if (!BigInteger.valueOf(42).equals(call(value, "getInteger", new Class<?>[0])))
          throw new AssertionError("Wrong contributed answer");
        Object negative = call(engine, "runSQWRLQuery", new Class<?>[]{String.class, String.class},
          "contributedNegative", "contributed:answer(41) -> sqwrl:select(41)");
        if (!Integer.valueOf(0).equals(call(negative, "getNumberOfRows", new Class<?>[0])))
          throw new AssertionError("Contributed negative control unexpectedly matched");
        System.out.println("PASS: actual extension registry discovers contributor; shared API identity; contributed answer = 42; negative control empty");
      }
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
      if (args.length == 4)
        call(engine, "createSWRLRule", new Class<?>[]{String.class, String.class},
          "contributedRule", "Person(?p) ^ contributed:answer(42) -> ContributedAdult(?p)");
      assertRuleRendering(plugin, ontology, args.length == 4);
      if (args.length >= 3) {
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
      Object contributed = call(engine, "runSQWRLQuery", new Class<?>[]{String.class, String.class},
        "contributedPeople", "ContributedAdult(?p) -> sqwrl:select(?p)");
      int expected = args.length == 4 ? 1 : 0;
      if (!Integer.valueOf(expected).equals(call(contributed, "getNumberOfRows", new Class<?>[0])))
        throw new AssertionError("Wrong contributed inference result count");
      if (expected == 1) {
        if (!Boolean.TRUE.equals(call(contributed, "next", new Class<?>[0])))
          throw new AssertionError("Missing contributed inference row");
        Object person = call(contributed, "getNamedIndividual", new Class<?>[]{int.class}, 0);
        if (!"urn:swrlapi:smoke#alice".equals(call(person, "getIRI", new Class<?>[0]).toString()))
          throw new AssertionError("Contributed rule inferred the wrong individual");
        System.out.println("PASS: contributed rule independently infers ContributedAdult(alice)");
      }
      call(owner, "close", new Class<?>[0]);
      System.out.println("PASS: packaged SWRLTab resolves; both tab classes load; rule rendering preserves prefixes and variables; SQWRL 2 + 3 = 5; rule infers Adult(alice)");
    } finally {
      Thread.currentThread().setContextClassLoader(originalLoader);
      framework.stop();
      framework.waitForStop(10000);
      // Keep isolated framework storage available for diagnosis; it never uses ~/.Protege.
      System.out.println("Felix diagnostics: " + storage);
    }
  }

  private static void startRegistry(Framework framework, Bundle plugin) throws Exception {
    for (String name : new String[]{"org.protege.common", "org.eclipse.equinox.common", "org.eclipse.equinox.supplement", "org.eclipse.equinox.registry"}) {
      Bundle match = null;
      for (Bundle bundle : framework.getBundleContext().getBundles())
        if (name.equals(bundle.getSymbolicName())) match = bundle;
      if (match == null) throw new AssertionError("Missing registry dependency " + name);
      match.start();
    }
    // Bootstrap only the host registry utility; starting the editor activator would launch the GUI.
    Class<?> utilities = plugin.loadClass("org.protege.editor.core.plugin.PluginUtilities");
    Object instance = utilities.getMethod("getInstance").invoke(null);
    utilities.getMethod("initialise", org.osgi.framework.BundleContext.class).invoke(instance, framework.getBundleContext());
    Object registry = call(instance, "getExtensionRegistry", new Class<?>[0]);
    if (registry == null) throw new AssertionError("Equinox extension registry did not start");
    Object point = call(registry, "getExtensionPoint", new Class<?>[]{String.class},
      "swrltab-plugin.SWRLBuiltInLibraryFactoryPlugin");
    if (point == null) throw new AssertionError("SWRLTab did not declare its extension point");
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

  private static void assertRuleRendering(Bundle plugin, Object ontology, boolean contributed) throws Exception {
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
    Object owner = plugin.loadClass("org.swrltab.core.SWRLTabEngineFactory").getConstructor().newInstance();
    try {
      call(owner, "createSWRLRuleEngine", new Class<?>[]{
        plugin.loadClass("org.semanticweb.owlapi.model.OWLOntology"),
        plugin.loadClass("org.swrlapi.core.IRIResolver")}, ontology, resolver);
      int matches = 0;
      int contributedMatches = 0;
      for (Object axiom : (Iterable<?>)call(ontology, "getAxioms", new Class<?>[0])) {
        String rendering = call(resolver, "render", new Class<?>[]{plugin.loadClass("org.semanticweb.owlapi.model.OWLObject")}, axiom).toString();
        if (rendering.equals("swrlb:add(?sum, 2, 3) -> sqwrl:select(?sum)")) matches++;
        if (rendering.equals("contributed:answer(?value) -> sqwrl:select(?value)")) contributedMatches++;
      }
      if (matches != 1) throw new AssertionError("Expected exactly one correctly rendered arithmetic query, got " + matches);
      if (contributedMatches != (contributed ? 1 : 0))
        throw new AssertionError("Contributed rendering did not use the declared library prefix");
    } finally {
      call(owner, "close", new Class<?>[0]);
    }
  }

  private static Object call(Object object, String name, Class<?>[] types, Object... values) throws Exception {
    Method method = object.getClass().getMethod(name, types);
    method.setAccessible(true);
    return method.invoke(object, values);
  }
}
