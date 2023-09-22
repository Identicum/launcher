FROM ghcr.io/identicum/centos7-java11-maven as build-env

WORKDIR /workspace/app
COPY pom.xml .
RUN mkdir src
COPY src ./src
RUN mvn clean package

# ############################################################################
# Build runtime image
FROM ghcr.io/identicum/centos7-java11

WORKDIR /app
COPY --from=build-env /workspace/app/target/launcher.jar .
EXPOSE 8080
CMD ["sh", "-c", "java -jar launcher.jar $APP_PARAMETERS"]
