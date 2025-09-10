
# Run import script:
poetry run python3 import.py

# Run chatbot service (local dev): 
ENV=dev poetry run fastapi dev main.py --reload

# Build Docker container (on host machine arch): 
docker build --tag rtci/rtci-ai .

# Run local dev environment (via docker-compose)
docker compose --env-file .env --file local-dev.yaml up

# Build production + push to docker hub:
docker system prune --all --force --volumes
docker buildx build --platform linux/amd64 --tag rtci/rtci-ai .
docker tag rtci/rtci-ai registry.digitalocean.com/umbrellabits/rtci/rtci-ai
docker push registry.digitalocean.com/umbrellabits/rtci/rtci-ai
