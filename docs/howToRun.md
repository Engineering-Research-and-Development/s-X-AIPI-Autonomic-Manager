## Prerequisites

### Docker and Docker Compose

**Docker** is an open platform for developing, shipping, and running applications. **Docker Compose** is a tool for defining and running multi-container Docker applications. To keep things simple both components will be run using [Docker](https://www.docker.com). **Docker** is a container technology which allows to different components isolated into their respective environments. 

- To install Docker on Windows follow the instructions [here](https://docs.docker.com/docker-for-windows/)
- To install Docker on Mac follow the instructions [here](https://docs.docker.com/docker-for-mac/)
- To install Docker on Linux follow the instructions [here](https://docs.docker.com/install/)

A docker-compose.yml file is used configure the required services for the application. This means all container services can be brought up in a single command. Docker Compose is installed by default as part of Docker for Windows and Docker for Mac, however Linux users will need to follow the instructions found [here](https://docs.docker.com/compose/install/)

You can check your current **Docker** and **Docker Compose** versions using the following commands:

```bash
docker-compose -v
docker version
```

### Postman

**Postman** is a collaboration platform for API development. Postman's features simplify each step of building an API and streamline collaboration, therefore you can create better APIs—faster. To install Postman, follow the instructions [here](https://www.postman.com/downloads).