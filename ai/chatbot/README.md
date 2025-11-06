
# Run chatbot service (local dev): 
ENV=dev poetry run fastapi dev main.py --reload

# Build Docker container (on host machine arch): 
docker build --tag rtci/rtci-ai .

# Run local dev environment (via docker-compose)
docker compose --env-file .env --file local-dev.yaml up
