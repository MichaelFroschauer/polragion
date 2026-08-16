
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

### Check the used system ressources of the docker containers
```bash
docker stats
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


# Certificates

Start backend server as https with certificates
```bash
uvicorn main:app `
  --host 0.0.0.0 `
  --port 8000 `
  --ssl-keyfile certs/lan-key.pem `
  --ssl-certfile certs/lan-cert.pem `
  --reload
```

Start frontend server as https with certificates. We can use vite also during development to proxy to our backend so only the frontend needs the certificates for https.
```typescript
export default defineConfig({
  plugins: [react()],

  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,

    https: {
      key: fs.readFileSync('./certs/lan-key.pem'),
      cert: fs.readFileSync('./certs/lan-cert.pem'),
    },

    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
```