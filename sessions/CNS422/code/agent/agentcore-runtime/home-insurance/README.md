# Home Insurance Agent


## Prerequisites
- Python 3.11+
- uv

Setup your python environment
```
source .venv/bin/activate
```

## Run locally

Run the agent
```
uv run home_insurance.py
```

Testing locally
```
uv run a2a_client.py http://localhost:9000 "Hi I'm customer CUST001, Tell me about my home insurance policy and claims"
```


## Run on AgentCore
Configure Agent (skip)
```
uvx --from bedrock-agentcore-starter-toolkit agentcore configure
```

Deploy Agent
```
uvx --from bedrock-agentcore-starter-toolkit agentcore launch
```

Follow the logs using the output of the above command

## Using MCP Inspector

Run mcp inspector
```
npx mcp-inspector@latest
```

Use the MCP Gateway URL:  https://reinvent-appmod-insurance-e1qpbpfbkt.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp

Generate Bearer Token
```
uv run get_cognito_token.py
```

Enter the Gateway URL and Bearer Token in Authorization header
