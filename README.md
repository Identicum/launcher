# launcher
This app is developed using the OAuth2 implementation of Spring Security (https://projects.spring.io/spring-security-oauth/docs/oauth2.html).

## Configure
In order to deploy the demo application, you need to configure a number of parameters in the [configuration file](src/main/resources/application.properties).
Some of those parameters are endpoint URLs of your IdP.
Additionally, you need to create your client application in your IdP and configure the client_id and client_secret.

## Build
The build process to compile the source code is based in Apache Maven.
To create the war file, go to the folder where you cloned the repository and run:

    mvn clean package

## Run

### WAR
To execute in a web container like Tomcat, simply copy the file to the webapps folder or deploy to your application server following standard procedures.

### Spring Boot
To build and run the code, in the folder where you cloned the repository, run:

    mvn spring-boot:run

### Docker
The app can run a as Docker container.
Dockerfile and instructions documented [here](docker/)
