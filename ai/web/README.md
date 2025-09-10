
# Run web (Vite) service (local dev): 
ENV=dev npm run dev

# Build single page + assets:
npm run build

# Test build locally: 
cd dist/
python3 -m http.server 8080
