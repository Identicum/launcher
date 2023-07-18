FROM ghcr.io/identicum/centos-java-maven as build-env

WORKDIR /workspace/app
COPY pom.xml .
RUN mkdir src
COPY src ./src
RUN mvn clean package

# ############################################################################
# Runtime image
FROM openjdk:8-jdk-alpine

WORKDIR /app
COPY --from=build-env /workspace/app/target/launcher.jar .
EXPOSE 8080
CMD ["sh", "-c", "java -jar launcher.jar $APP_PARAMETERS"]
