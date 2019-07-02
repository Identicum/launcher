# launcher
OAuth2 app using Java Spring security.

## Source
Source code can be found at: https://github.com/Identicum/launcher

## Usage

### Install

Pull `identicum/launcher` from the Docker repository:

    docker pull identicum/launcher:latest


Or build `identicum/launcher` from source:

    git clone https://github.com/Identicum/launcher.git
    cd launcher/docker
    docker build -t identicum/launcher .

### Run

#### Customize your application.properties
* Get base file from https://github.com/Identicum/launcher/blob/master/src/main/resources/application.properties
* Customize to your environment

#### Run the container
Run the image, binding associated ports, and mounting your custom application.properties and data directory (for the H2 database):

    docker run -p 8080:8080 -v $(pwd)/application.properties:/usr/local/tomcat/webapps/launcher/WEB-INF/classes/application.properties:ro -v $(pwd)/data:/data identicum/launcher:latest
