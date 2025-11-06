## Architecture 
The chatbot user interface (UI) is a static single-page Vite application.  For more information on Vite, see https://vite.dev/guide/index.html.

- The UI style is managed via Tailwind CSS and base 'style.css' with hard-coded colors.
- The UI script is a single Typescript file 'main.ts' which controls submitting requests and processing responses between the UI and chatbot backend service.

## Configuration
The chatbot UI is configured via environment variables or the '.env' file.  For local testing, you should use the '.env.development' file and 'npm run dev'.

- VITE_SERVER_URL - the base URL of the chatbot backend service.

## Deployment
The chatbot UI is designed to be embedded within the larger RTCI site as a single-page application.   

- Run the 'build.sh' script to build the UI web application.
- The UI is built and copied into a directory specified by the environment variable 'DESTINATION' (defaults to relative folder '../../docs/ai').
