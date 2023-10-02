FROM ghcr.io/identicum/alpine-jdk17-maven:latest as build-env

WORKDIR /workspace/app
COPY pom.xml .
RUN mkdir src
COPY src ./src
RUN mvn clean package

# ############################################################################
# Build runtime image
FROM ghcr.io/identicum/alpine-jre17:latest

WORKDIR /app
COPY --from=build-env /workspace/app/target/launcher.jar .
EXPOSE 8080

RUN apk add --no-cache curl
HEALTHCHECK --timeout=5s CMD curl --fail http://localhost:8080/imgs/favicon-32.png || exit 1

CMD ["sh", "-c", "java -jar launcher.jar $APP_PARAMETERS"]
