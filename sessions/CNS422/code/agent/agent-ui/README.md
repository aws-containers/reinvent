# Test Agent UI

## Run locally

Setup python
```
source .venv/bin/activate
```

The deployment automatically loads environment variables from `.env`:

```bash
CLIENT_ID=your-client-id
AGENT_USERNAME=your-username
AGENT_USER_PASSWORD=your-password
AGENT_ARN=your-agent-arn
```

```
uv run ui
```

## Deploy to ECS

TLRD;
```
./deploy.sh
```

Follow the instructions in [DEPLOYMENT.md](DEPLOYMENT.md)

