## SWRLTab Build Project

This project contains a Maven POM that builds a core set of SWRLAPI- and SWRLTab-related components.
Currently it builds the [SWRLAPI](https://github.com/protegeproject/swrlapi.git), 
the [SWRLAPI Drools Engine](https://github.com/protegeproject/swrlapi-drools-engine.git), 
the standalone [SWRLTab](https://github.com/protegeproject/swrltab.git) application, 
and the [Protégé SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git).

#### Prerequisites

To run the build process in this project, you must have the following items installed:

+ A tool for checking out a [Git](http://git-scm.com/) repository.
+ Apache's [Maven](http://maven.apache.org/index.html).
+ [Java 8](http://www.oracle.com/technetwork/java/javase/downloads/index.html)

#### Building

Create a suitable local directory and then clone the core SWRLAPI- and SWRLTab-related projects as follows:

    git clone https://github.com/protegeproject/swrlapi.git
    git clone https://github.com/protegeproject/swrlapi-drools-engine.git
    git clone https://github.com/protegeproject/swrltab.git
    git clone https://github.com/protegeproject/swrltab-plugin.git
    git clone https://github.com/protegeproject/swrltab-project.git
    git clone https://github.com/protegeproject/swrlapi-integration-tests.git

Change into the SWRLTab project directory:

    cd swrltab-project

And then build everything with Maven:

    mvn clean install

The SWRLAPI integration tests can take quite a while to run. You can skip them as follows:

    mvn -DskipTests=true clean install

Documentation for the SWRLAPI library can be found [here](https://github.com/protegeproject/swrlapi/wiki).
See the documentation for the [Protégé SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git) for details on installing the generated SWRLTab plugin in your local Protégé installation.

#### License

The software is licensed under the [BSD 2-clause License](https://github.com/protegeproject/swrltab-project/blob/master/license.txt).

