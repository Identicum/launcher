FROM identicum/centos-java-maven:latest AS build-env

COPY source .
RUN /usr/bin/mvn package

# ############################################################################
# Build runtime image
FROM identicum/centos-tomcat:latest
MAINTAINER Gustavo J Gallardo <ggallard@identicum.com>

RUN yum -y install unzip
COPY --from=build-env /source/target/launcher-0.0.1-SNAPSHOT.war /tmp/launcher.war
RUN unzip -qq /tmp/launcher.war -d /usr/local/tomcat/webapps/launcher && \
    rm -f /tmp/launcher.war
