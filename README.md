## SWRLAPI Build Project

This project contains a Maven POM that builds a core set of SWRLAPI-related components.
Currently it builds the [SWRLAPI](https://github.com/protegeproject/swrlapi.git), 
the [SWRLAPI Drools Engine](https://github.com/protegeproject/swrlapi-drools-engine.git), 
the [SWRLAPI Example](https://github.com/protegeproject/swrlapi-example.git) project, 
the [SWRLAPI Integration Tests](https://github.com/protegeproject/swrlapi-integration-tests.git) project, 
the standalone [SWRLTab](https://github.com/protegeproject/swrltab.git) application, 
and the [Protégé SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git).

#### Building

To run the build process in this project, you must have the following items installed:

+ [Java 11](https://www.oracle.com/java/technologies/downloads/archive/) or later
+ A tool for checking out a [Git](https://git-scm.com/) repository
+ Apache's [Maven](https://maven.apache.org/index.html)
+ A Protégé (5.6.4 or higher) distribution. Download [here](https://protege.stanford.edu/products.php#desktop-protege).

Create a suitable local directory and then clone the core SWRLAPI-related projects as follows:

    git clone https://github.com/protegeproject/swrlapi-parent.git
    git clone https://github.com/protegeproject/swrlapi-project.git
    git clone https://github.com/protegeproject/swrlapi.git
    git clone https://github.com/protegeproject/swrlapi-drools-engine.git
    git clone https://github.com/protegeproject/swrlapi-example.git
    git clone https://github.com/protegeproject/swrlapi-integration-tests.git
    git clone https://github.com/protegeproject/swrltab.git
    git clone https://github.com/protegeproject/swrltab-plugin.git

Change into the SWRLAPI parent directory:

    cd swrlapi-parent

And then build the parent project with Maven:

    mvn clean install

Then change into the project directory:

    cd ../swrlapi-project

And then build everything with Maven:

    mvn clean install

The SWRLAPI integration tests can take quite a while to run. You can skip them as follows:

    mvn -DskipTests=true clean install

Documentation for the SWRLAPI library can be found [here](https://github.com/protegeproject/swrlapi/wiki).
See the documentation for the [Protégé SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git) for details on installing the generated SWRLTab plugin in your local Protégé installation.

#### License

The software is licensed under the [BSD 2-clause License](https://github.com/protegeproject/swrltab-project/blob/master/license.txt).

#### Questions

If you have questions about this project, please go to the main
Protégé website and subscribe to the [Protégé Developer Support
mailing list](http://protege.stanford.edu/support.php#mailingListSupport).
After subscribing, send messages to protege-dev at lists.stanford.edu.
