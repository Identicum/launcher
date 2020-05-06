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

To override some properties add them to the command line:

    mvn spring-boot:run -Dspring-boot.run.arguments="--app.homedir=/var/opt/identicum/launcher"

### Docker
The app can run a as Docker container.
Dockerfile and instructions documented [here](docker/)

## Initial dataset
When the app starts and there is no data, it tries to find a file with initial dataset under `${app.homedir}/data.json`

The default value for `${app.homedir}` is `/var/opt/identicum/launcher`. Remember you can also override this property value at runtime.

Sample data:
```json
[
    {
      "color": "#ff0000",
      "display": "Display 1",
      "icon": "fa fa-launcher",
      "roleNames": [
        "role-1",
        "role-2"
      ],
      "target": "target"
    }, 
    {
      "color": "#ff0000",
      "display": "Display 2",
      "icon": "fa fa-launcher",
      "roleNames": [
        "role-1"
      ],
      "target": "target"
    } 
 ]
```


### Loading properties from external file
You can store launcher properties in an external file and then reference this file when running spring-boot:

    mvn spring-boot:run -Dspring.config.location=/var/opt/identicum/launcher/application.properties