FROM identicum/centos-java-maven as build-env

WORKDIR /workspace/app
COPY pom.xml .
RUN mkdir src
COPY src ./src
RUN mvn clean package

EXPOSE 8080
CMD ["mvn", "spring-boot:run"]
