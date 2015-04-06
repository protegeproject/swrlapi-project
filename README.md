## SWRLTab Build Project

This project contains a Maven POM that builds a core set of SWRLAPI- and SWRLTab-related projects.
Currently it builds the [SWRLAPI](https://github.com/protegeproject/swrlapi.git), 
the [SWRLAPI Drools Engine](https://github.com/protegeproject/swrlapi-drools-engine.git), 
the standalone [SWRLTab](https://github.com/protegeproject/swrltab.git) application, 
and the [Protege SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git).

#### Prerequisites

To run the build process in this project, you must have the following items installed:

+ Apache's [Maven](http://maven.apache.org/index.html).
+ A tool for checking out a [Git](http://git-scm.com/) repository.

#### Building

Create a suitable local directory and then clone the core SWRLAPI- and SWRLTab-related projects as follows:

    git clone https://github.com/protegeproject/swrlapi.git
    git clone https://github.com/protegeproject/swrlapi-drools-engine.git
    git clone https://github.com/protegeproject/swrltab.git
    git clone https://github.com/protegeproject/swrltab-plugin.git
    git clone https://github.com/protegeproject/swrltab-project.git

Change into the SWRLTab Project directory:

    cd swrltab-project

Build everything with Maven:

    mvn clean install

See the documentation for the [Protégé SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git) for details on installing the generated SWRLTab plugin in your local Protégé installation.

