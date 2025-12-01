# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG RUNTAG=latest
FROM cgr.dev/chainguard/python:latest-dev AS uv

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Prefer the system python
ENV UV_PYTHON_PREFERENCE=only-system

# Copy the required files first (from infrastructure directory context)
COPY pyproject.toml uv.lock ./

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev --no-editable

# Copy only the necessary source code
COPY shared/ ./shared/
COPY mock_data/ ./mock_data/
COPY mcp_servers/technician_server/ ./mcp_servers/technician_server/

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable

FROM cgr.dev/chainguard/python:${RUNTAG}

# Project got copied to here
WORKDIR /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Get the project from the uv layer
COPY --from=uv /app/.venv .venv

# Copy only the necessary source code and configuration files
COPY shared/ ./shared/
COPY mock_data/ ./mock_data/
COPY mcp_servers/technician_server/ ./mcp_servers/technician_server/

# Expose the REST API port for technician server
EXPOSE 8003

# Use the technician REST server entry point
ENTRYPOINT ["technician-rest-server"]
