
## Run GitHub client
docker run --name copilot-cli -p 4321:4321 copilot-cli:latest --headless --host 0.0.0.0 --port 4321

## Run Qdrant vector database
sudo docker run -p 6333:6333 -p 6334:6334 -v "$(pwd)/qdrant_storage:/qdrant/storage:z" qdrant/qdrant


