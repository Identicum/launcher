FROM identicum/centos-java-maven:latest AS build-env

RUN git clone https://github.com/Identicum/launcher .
RUN /usr/bin/mvn package

# ############################################################################
# Build runtime image
FROM identicum/centos-tomcat:latest

RUN yum -y install unzip
COPY --from=build-env /source/target/launcher-0.0.1-SNAPSHOT.war /tmp/launcher.war
RUN unzip -qq /tmp/launcher.war -d /usr/local/tomcat/webapps/launcher && \
    rm -f /tmp/launcher.war

RUN echo "<% response.sendRedirect(\"/launcher/\"); %>" > webapps/ROOT/index.jsp
