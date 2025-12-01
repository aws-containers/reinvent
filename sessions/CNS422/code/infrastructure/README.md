# Insurance Agent ChatBot - Infrastructure Component

This component contains MCP servers and shared utilities for backend services supporting the insurance agent demo system.

## Setup

1. Create and activate virtual environment:
   ```bash
   ./setup_venv.sh
   source venv/bin/activate
   ```

2. Set environment variables:
   ```bash
   # For development
   cp ../.env.development .env

   # For demo
   cp ../.env.demo .env
   ```

## Project Structure

```
infrastructure/
├── mcp_servers/
│   ├── appointment_server/    # Appointment management MCP server
│   ├── technician_server/     # Technician tracking MCP server
│   └── customer_server/       # Customer information MCP server
├── shared/                    # Shared models and utilities
├── config.py                  # Configuration management
├── pyproject.toml            # Dependencies and build config
├── setup_venv.sh             # Virtual environment setup
└── README.md                 # This file
```

## MCP Servers

### Appointment Server (Port 8001)
- Manages appointment scheduling and updates
- Handles availability checking and conflict detection

### Technician Server (Port 8002)
- Tracks technician locations and status
- Provides ETA calculations and availability

### Customer Server (Port 8003)
- Manages customer profiles and policy information
- Handles claim creation and history

## Development

- Run tests: `pytest`
- Format code: `black .`
- Sort imports: `isort .`
- Type checking: `mypy .`

## Configuration

Each server uses environment-specific configuration from `config.py`. Settings include:

- Server host and port bindings
- Data directory locations
- Mock data settings
- Logging configuration
