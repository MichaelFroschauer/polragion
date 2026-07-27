
# Setup Docker Environment

All following commands should be executed from the `./Polragion/docker` directory.

### Create a .env file from the example and fill in the secrets
```bash
cp .env.example .env
```

### Build the docker images and start the containers
```bash
docker compose -f docker-compose.yaml up -d --build
```

### See the logs of the containers
```bash
docker compose logs -f
```

### Check the status / health check of the containers
```bash
docker compose ps
```

### Stop the containers, the data is saved in the host volumes
```bash
docker compose  -f docker-compose.yaml down
```



# Single Docker Commands

### Build docker image for backend
```bash
cd ./Polragion
docker build -f docker/polragion-backend.Dockerfile -t polragion-backend:latest polragion-backend
```

### Build docker image for frontend#
```bash
cd ./Polragion
docker build -f docker/polragion-frontend.Dockerfile -t polragion-frontend:latest polragion-frontend
```
