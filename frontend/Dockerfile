FROM node:20-bookworm-slim

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /workspace/frontend

COPY frontend/package.json /workspace/frontend/package.json
RUN npm install

COPY frontend /workspace/frontend

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
