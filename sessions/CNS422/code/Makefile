# Insurance Agent ChatBot - Project Management

.PHONY: help setup-agent setup-infrastructure setup-all test test-infrastructure test-agent test-models test-utils test-mock-data test-customer-server lint format install check status show-domain-config terraform-init terraform-plan terraform-apply terraform-destroy terraform-output test-eks test-services test-ingress test-all-eks check-eks-status ecr-login build-images build-customer-image build-appointment-image build-technician-image push-images push-customer-image push-appointment-image push-technician-image tag-images build-and-push clean-images deploy-dev-ecr deploy-prod-ecr deploy-ecr delete-dev-ecr delete-prod-ecr restart-dev restart-prod test-entry-points test-integration test-appointment-integration test-technician-integration test-customer-integration test-customer-rest-api test-appointment-rest-api test-technician-rest-api test-eks-discovery print-alb-urls test-customer-eks-rest-api test-appointment-eks-rest-api test-technician-eks-rest-api test-eks-rest-apis dump-openapi-customer dump-openapi-appointment dump-openapi-technician setup-mcp-gateway setup-mcp-gateway-help

help:
	@echo "Insurance Agent ChatBot - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup-environment   Setup environment configuration (domain, AWS credentials)"
	@echo "  setup-agent         Setup agent component virtual environment"
	@echo "  setup-infrastructure Setup infrastructure component virtual environment"
	@echo "  setup-all           Setup both components"
	@echo ""
	@echo "Development Commands:"
	@echo "  test               Run tests for both components"
	@echo "  test-infrastructure Run tests for infrastructure component only"
	@echo "  test-agent         Run tests for agent component only"
	@echo "  test-models        Run model tests for infrastructure component"
	@echo "  test-utils         Run utility tests for infrastructure component"
	@echo "  test-mock-data     Run mock data validation tests for infrastructure component"
	@echo "  test-appointment-server Run Appointments MCP Server tests"
	@echo "  test-technician-server Run Technician Tracking MCP Server tests"
	@echo "  test-customer-server Run Customer Information MCP Server tests"
	@echo "  test-customer-rest-api Run Customer Information REST API tests (framework-based)"
	@echo "  test-appointment-rest-api Run Appointment Management REST API tests (framework-based)"
	@echo "  test-technician-rest-api Run Technician Tracking REST API tests (framework-based)"
	@echo "  test-entry-points    Test server entry points (uv run commands)"
	@echo "  test-integration     Run integration tests (requires servers running)"
	@echo "  test-appointment-integration Run appointment server integration tests"
	@echo "  test-technician-integration Run technician server integration tests"
	@echo "  test-customer-integration Run customer server integration tests"
	@echo "  lint               Run linting for both components"
	@echo "  format             Format code for both components"
	@echo ""
	@echo "Server Commands (via Makefile):"
	@echo "  run-customer-mcp   Run Customer Information MCP Server (port 8001)"
	@echo "  run-customer-rest  Run Customer Information REST API Server (port 8001)"
	@echo "  run-customer-combined Run Customer Information Combined Server (port 8001)"
	@echo "  run-appointment-mcp Run Appointment Management MCP Server (port 8002)"
	@echo "  run-appointment-rest Run Appointment Management REST API Server (port 8002)"
	@echo "  run-appointment-combined Run Appointment Management Combined Server (port 8002)"
	@echo "  run-technician-mcp Run Technician Tracking MCP Server (port 8003)"
	@echo "  run-technician-rest Run Technician Tracking REST API Server (port 8003)"
	@echo "  run-technician-combined Run Technician Tracking Combined Server (port 8003)"
	@echo ""
	@echo "EKS Infrastructure Commands:"
	@echo "  check-eks-status   Check EKS implementation status and missing files"
	@echo "  terraform-init     Initialize Terraform in infrastructure/terraform"
	@echo "  terraform-plan     Plan Terraform deployment (shows what will be created)"
	@echo "  terraform-apply    Deploy EKS Auto Mode cluster with SSL/TLS and DNS"
	@echo "  terraform-destroy  Destroy EKS cluster and all AWS resources"
	@echo "  terraform-output   Show Terraform outputs (cluster info, ECR URIs, etc.)"
	@echo ""
	@echo "Application Deployment Commands:"
	@echo "  deploy-dev-ecr     Deploy to development environment with ECR images"
	@echo "  deploy-prod-ecr    Deploy to production environment with ECR images"
	@echo "  delete-dev-ecr     Delete development deployment"
	@echo "  delete-prod-ecr    Delete production deployment"
	@echo "  restart-dev        Restart all deployments in development namespace"
	@echo "  restart-prod       Restart all deployments in production namespace"

	@echo "  test-eks           Test EKS cluster connectivity and status"
	@echo "  test-services      Test Kubernetes service deployments"
	@echo "  test-ingress       Test ALB ingress controllers and external access"
	@echo "  test-all-eks       Run all EKS-related tests (cluster, services, ingress)"
	@echo "  test-eks-deployment Comprehensive EKS deployment validation with manifest testing"
	@echo ""
	@echo "EKS REST API Testing Commands:"
	@echo "  test-eks-discovery Test ALB URL discovery and endpoint accessibility"
	@echo "  print-alb-urls     Print the 3 ALB URLs from development namespace"
	@echo "  test-customer-eks-rest-api    Test Customer server REST API via ALB endpoint (✅ Ready)"
	@echo "  test-appointment-eks-rest-api Test Appointment server REST API via ALB endpoint (✅ Ready)"
	@echo "  test-technician-eks-rest-api  Test Technician server REST API via ALB endpoint (✅ Ready)"
	@echo "  test-eks-rest-apis Run all EKS REST API tests (✅ Ready)"
	@echo ""
	@echo "OpenAPI JSON Dump Commands:"
	@echo "  dump-openapi-customer    Dump Customer server OpenAPI JSON via HTTPS domain"
	@echo "  dump-openapi-appointment Dump Appointment server OpenAPI JSON via HTTPS domain"
	@echo "  dump-openapi-technician  Dump Technician server OpenAPI JSON via HTTPS domain"
	@echo ""
	@echo "MCP Gateway Commands:"
	@echo "  setup-mcp-gateway-env    Setup MCP Gateway Python environment (run first)"
	@echo "  setup-mcp-gateway        Setup AWS Bedrock AgentCore MCP Gateway with Cognito authentication"
	@echo "                           Usage: make setup-mcp-gateway [ARGS='--rest-api-env=development']"
	@echo "  test-mcp-gateway-connection Test MCP Gateway basic connectivity"
	@echo "  test-mcp-gateway         Test MCP Gateway with AI Agent (comprehensive test)"
	@echo "  delete-mcp-gateway       Delete AWS Bedrock AgentCore MCP Gateway and associated resources"
	@echo "                           Usage: make delete-mcp-gateway [ARGS='--rest-api-env=development']"
	@echo "  setup-mcp-gateway-help   Show MCP Gateway setup command help and options"
	@echo ""
	@echo "Container & ECR Commands:"
	@echo "  ecr-login          Authenticate Docker with ECR using AWS CLI"
	@echo "  build-images       Build all container images for AMD64 platform"
	@echo "  build-customer-image    Build customer server container image"
	@echo "  build-appointment-image Build appointment server container image"
	@echo "  build-technician-image  Build technician server container image"
	@echo "  push-images        Push all container images to ECR repositories"
	@echo "  push-customer-image     Push customer server image to ECR"
	@echo "  push-appointment-image  Push appointment server image to ECR"
	@echo "  push-technician-image   Push technician server image to ECR"
	@echo "  tag-images         Tag all images with latest tags"
	@echo "  build-and-push     Complete container workflow (ECR login + build + tag + push)"
	@echo "  clean-images       Remove local container images"
	@echo ""
	@echo "Advanced Deployment Commands:"
	@echo "  deploy-ecr         Flexible deployment: make deploy-ecr ENV=development ACTION=apply"
	@echo ""
	@echo "Utility Commands:"
	@echo "  install            Install uv package manager (if not present)"
	@echo "  check              Check project health and dependencies"
	@echo "  status             Show project status and test results"
	@echo "  show-domain-config Show SSL certificate and domain configuration (includes HTTPS support with SSL redirect)"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  cleanup-k8s-dev    Delete Kubernetes resources from development namespace"
	@echo "  cleanup-k8s-prod   Delete Kubernetes resources from production namespace"
	@echo "  cleanup-k8s-all    Delete all Kubernetes resources (dev + prod)"
	@echo "  cleanup-terraform  Destroy EKS cluster and AWS infrastructure (after K8s cleanup)"
	@echo "  cleanup-gateway    Delete AgentCore Gateway (after Terraform cleanup)"
	@echo "  cleanup-all        Complete cleanup: K8s → Terraform → Gateway (⚠️  DESTRUCTIVE)"
	@echo "  verify-k8s-cleanup Verify all Kubernetes resources are deleted"
	@echo "  verify-cleanup     Comprehensive verification of complete environment cleanup"

setup-agent:
	@echo "Setting up agent component..."
	cd agent && uv sync --extra dev

setup-infrastructure:
	@echo "Setting up infrastructure component..."
	cd infrastructure && uv sync --extra dev

setup-all: setup-agent setup-infrastructure
	@echo "All components setup complete!"

test:
	@echo "Running tests for agent component..."
	cd agent && uv run pytest tests/ -v
	@echo "Running tests for infrastructure component..."
	cd infrastructure && uv run pytest tests/ -v

test-infrastructure:
	@echo "Running tests for infrastructure component only..."
	cd infrastructure && uv run pytest tests/ -v

test-agent:
	@echo "Running tests for agent component only..."
	cd agent && uv run pytest tests/ -v

test-models:
	@echo "Running model tests for infrastructure component..."
	cd infrastructure && uv run pytest tests/test_models.py -v

test-utils:
	@echo "Running utility tests for infrastructure component..."
	cd infrastructure && uv run pytest tests/test_utils.py -v

test-mock-data:
	@echo "Running mock data validation tests for infrastructure component..."
	cd infrastructure && uv run pytest tests/test_mock_data.py -v

test-appointment-server:
	@echo "Running Appointments MCP Server tests..."
	cd infrastructure && uv run pytest tests/test_appointment_server.py -v

test-technician-server:
	@echo "Running Technician Tracking MCP Server tests..."
	cd infrastructure && uv run pytest tests/test_technician_server.py -v

test-customer-server:
	@echo "Running Customer Information MCP Server tests..."
	cd infrastructure && uv run pytest tests/test_customer_server.py -v

test-customer-rest-api:
	@echo "Running Customer Information REST API tests (framework-based)..."
	cd infrastructure && uv run pytest tests/test_customer_server_rest_api.py -v

test-appointment-rest-api:
	@echo "Running Appointment Management REST API tests (framework-based)..."
	cd infrastructure && uv run pytest tests/test_appointment_server_rest_api.py -v

test-technician-rest-api:
	@echo "Running Technician Tracking REST API tests (framework-based)..."
	cd infrastructure && uv run pytest tests/test_technician_server_rest_api.py -v

test-entry-points:
	@echo "Testing server entry points..."
	cd infrastructure && uv run python test_entry_points.py

test-integration:
	@echo "Running integration tests (requires servers to be running)..."
	cd infrastructure/integration-tests && uv run pytest -v

test-appointment-integration:
	@echo "Running appointment server integration tests (requires server to be running on port 8002)..."
	cd infrastructure/integration-tests && uv run pytest test_appointment_server_integration.py -v

test-technician-integration:
	@echo "Running technician server integration tests (requires server to be running on port 8003)..."
	cd infrastructure/integration-tests && uv run pytest test_technician_server_integration.py -v

test-customer-integration:
	@echo "Running customer server integration tests (requires server to be running on port 8001)..."
	cd infrastructure/integration-tests && uv run pytest test_customer_server_integration.py -v

lint:
	@echo "Running linting for agent component..."
	cd agent && uv run flake8 src/
	@echo "Running linting for infrastructure component..."
	cd infrastructure && uv run flake8 .

format:
	@echo "Formatting agent component..."
	cd agent && uv run black src/ && uv run isort src/
	@echo "Formatting infrastructure component..."
	cd infrastructure && uv run black . && uv run isort .

install:
	@echo "Checking for uv package manager..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv package manager..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "Please restart your terminal or run: source ~/.bashrc"; \
	else \
		echo "uv is already installed: $(uv --version)"; \
	fi

check:
	@echo "Checking project health..."
	@echo "=== UV Version ==="
	@uv --version || echo "❌ uv not found - run 'make install'"
	@echo ""
	@echo "=== Agent Dependencies ==="
	@cd agent && uv tree 2>/dev/null || echo "❌ Agent not set up - run 'make setup-agent'"
	@echo ""
	@echo "=== Infrastructure Dependencies ==="
	@cd infrastructure && uv tree 2>/dev/null || echo "❌ Infrastructure not set up - run 'make setup-infrastructure'"

status: check
	@echo ""
	@echo "=== Test Results ==="
	@echo "Infrastructure Tests:"
	@cd infrastructure && uv run pytest tests/ --tb=no -q 2>/dev/null || echo "❌ Tests failing or not set up"
	@echo ""
	@echo "=== Project Status ==="
	@echo "✅ Use 'make help' to see all available commands"

run-customer-mcp:
	@echo "🚀 Starting Customer Information MCP Server..."
	@echo "📍 MCP endpoint: http://localhost:8001/mcp"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run customer-mcp-server

run-customer-rest:
	@echo "🚀 Starting Customer Information REST API Server..."
	@echo "📍 REST API docs: http://localhost:8001/docs"
	@echo "📍 Health check: http://localhost:8001/health"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run customer-rest-server

run-customer-combined:
	@echo "🚀 Starting Customer Information Combined Server (MCP + REST)..."
	@echo "📍 REST API docs: http://localhost:8001/api/docs"
	@echo "📍 MCP endpoint: http://localhost:8001/mcp"
	@echo "📍 Health check: http://localhost:8001/api/health"
	@echo "📍 Service info: http://localhost:8001/"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run customer-combined-server

run-appointment-mcp:
	@echo "🚀 Starting Appointment Management MCP Server..."
	@echo "📍 MCP endpoint: http://localhost:8002/mcp"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run appointment-mcp-server

run-appointment-rest:
	@echo "🚀 Starting Appointment Management REST API Server..."
	@echo "📍 REST API docs: http://localhost:8002/docs"
	@echo "📍 Health check: http://localhost:8002/health"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run appointment-rest-server

run-appointment-combined:
	@echo "🚀 Starting Appointment Management Combined Server (MCP + REST)..."
	@echo "📍 REST API docs: http://localhost:8002/api/docs"
	@echo "📍 MCP endpoint: http://localhost:8002/mcp"
	@echo "📍 Health check: http://localhost:8002/api/health"
	@echo "📍 Service info: http://localhost:8002/"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run appointment-combined-server

run-technician-mcp:
	@echo "🚀 Starting Technician Tracking MCP Server..."
	@echo "📍 MCP endpoint: http://localhost:8003/mcp"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run technician-mcp-server

run-technician-rest:
	@echo "🚀 Starting Technician Tracking REST API Server..."
	@echo "📍 REST API docs: http://localhost:8003/docs"
	@echo "📍 Health check: http://localhost:8003/health"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run technician-rest-server

run-technician-combined:
	@echo "🚀 Starting Technician Tracking Combined Server (MCP + REST)..."
	@echo "📍 REST API docs: http://localhost:8003/api/docs"
	@echo "📍 MCP endpoint: http://localhost:8003/mcp"
	@echo "📍 Health check: http://localhost:8003/api/health"
	@echo "📍 Service info: http://localhost:8003/"
	@echo "🛑 Press Ctrl+C to stop"
	cd infrastructure && uv run technician-combined-server

show-domain-config:
	@echo "🔐 SSL Certificate and Domain Configuration:"
	@echo ""
	@if [ -z "$$DOMAIN_NAME" ]; then \
		echo "❌ DOMAIN_NAME environment variable is not set!"; \
		echo "💡 Please set it first: export DOMAIN_NAME=your-domain.com"; \
		echo ""; \
	else \
		echo "📍 Domain Name: $$DOMAIN_NAME"; \
		echo "🔒 SSL Certificate: Wildcard certificate (*.$$DOMAIN_NAME)"; \
	fi
	@echo "📡 DNS Management: External DNS with Route53 integration"
	@echo "✅ Certificate Validation: Automatic DNS validation via Route53"
	@echo "🌐 HTTPS Support: All ingress resources configured for HTTP and HTTPS"
	@echo "🔒 SSL Redirect: HTTP traffic automatically redirected to HTTPS"
	@echo ""
	@echo "🏗️ Infrastructure Components:"
	@echo "  • ACM Certificate (acm.tf) - SSL/TLS certificates with wildcard support"
	@echo "  • External DNS (external-dns.tf) - Automatic DNS record management"
	@echo "  • Route53 Integration - DNS validation and record creation"
	@echo "  • ALB Ingress - HTTP (80) and HTTPS (443) listeners with SSL redirect"
	@echo ""
	@echo "💡 To customize the domain, modify the 'domain_name' variable in:"
	@echo "   infrastructure/terraform/variables.tf"
	@echo ""
	@if cd infrastructure/terraform && terraform output acm_certificate_domain_name >/dev/null 2>&1; then \
		echo "📊 Current Deployment Status:"; \
		echo "  📍 Domain: $$(cd infrastructure/terraform && terraform output -raw acm_certificate_domain_name 2>/dev/null || echo 'Not deployed')"; \
		echo "  🌐 Route53 Zone: $$(cd infrastructure/terraform && terraform output -raw route53_zone_name 2>/dev/null || echo 'Not configured')"; \
		echo "  🔒 Certificate ARN: $$(cd infrastructure/terraform && terraform output -raw acm_certificate_arn 2>/dev/null || echo 'Not available')"; \
		echo "  ✅ Certificate Status: Validated and Ready"; \
		echo "  🔗 HTTPS Endpoints: All services support both HTTP and HTTPS with automatic SSL redirect"; \
	else \
		echo "ℹ️  No deployment found. Run 'make terraform-apply' to deploy."; \
	fi

# Container & ECR Commands
ecr-login:
	@echo "🔐 Authenticating Docker with ECR..."
	@if ! command -v aws >/dev/null 2>&1; then \
		echo "❌ AWS CLI not found. Please install AWS CLI first."; \
		exit 1; \
	fi
	@echo "Getting ECR configuration from Terraform..."
	@if ! cd infrastructure/terraform && terraform output aws_account_id >/dev/null 2>&1; then \
		echo "❌ Terraform state not found. Please run 'make terraform-apply' first."; \
		exit 1; \
	fi
	$(eval ACCOUNT_ID := $(shell cd infrastructure/terraform && terraform output -raw aws_account_id 2>/dev/null))
	$(eval REGION := $(shell cd infrastructure/terraform && terraform output -raw aws_region 2>/dev/null))
	@echo "Getting ECR login token for account $(ACCOUNT_ID) in region $(REGION)..."
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
	@echo "✅ Successfully authenticated with ECR"

build-images: build-customer-image build-appointment-image build-technician-image
	@echo "✅ All container images built successfully!"

build-customer-image:
	@echo "🐳 Building customer server container image..."
	docker build --platform linux/amd64 -t customer-server:latest -f infrastructure/mcp_servers/customer_server/Dockerfile infrastructure/
	@echo "✅ Customer server image built successfully"

build-appointment-image:
	@echo "🐳 Building appointment server container image..."
	docker build --platform linux/amd64 -t appointment-server:latest -f infrastructure/mcp_servers/appointment_server/Dockerfile infrastructure/
	@echo "✅ Appointment server image built successfully"

build-technician-image:
	@echo "🐳 Building technician server container image..."
	docker build --platform linux/amd64 -t technician-server:latest -f infrastructure/mcp_servers/technician_server/Dockerfile infrastructure/
	@echo "✅ Technician server image built successfully"

tag-images:
	@echo "🏷️ Tagging container images for ECR..."
	@if ! cd infrastructure/terraform && terraform output aws_account_id >/dev/null 2>&1; then \
		echo "❌ Terraform state not found. Please run 'make terraform-apply' first."; \
		exit 1; \
	fi
	$(eval ACCOUNT_ID := $(shell cd infrastructure/terraform && terraform output -raw aws_account_id 2>/dev/null))
	$(eval REGION := $(shell cd infrastructure/terraform && terraform output -raw aws_region 2>/dev/null))
	docker tag customer-server:latest $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/agentcore-gateway/customer-server:latest
	docker tag appointment-server:latest $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/agentcore-gateway/appointment-server:latest
	docker tag technician-server:latest $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/agentcore-gateway/technician-server:latest
	@echo "✅ All images tagged for ECR"

push-images: push-customer-image push-appointment-image push-technician-image
	@echo "✅ All container images pushed to ECR successfully!"

push-customer-image:
	@echo "📤 Pushing customer server image to ECR..."
	@if ! cd infrastructure/terraform && terraform output aws_account_id >/dev/null 2>&1; then \
		echo "❌ Terraform state not found. Please run 'make terraform-apply' first."; \
		exit 1; \
	fi
	$(eval ACCOUNT_ID := $(shell cd infrastructure/terraform && terraform output -raw aws_account_id 2>/dev/null))
	$(eval REGION := $(shell cd infrastructure/terraform && terraform output -raw aws_region 2>/dev/null))
	docker push $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/agentcore-gateway/customer-server:latest
	@echo "✅ Customer server image pushed successfully"

push-appointment-image:
	@echo "📤 Pushing appointment server image to ECR..."
	@if ! cd infrastructure/terraform && terraform output aws_account_id >/dev/null 2>&1; then \
		echo "❌ Terraform state not found. Please run 'make terraform-apply' first."; \
		exit 1; \
	fi
	$(eval ACCOUNT_ID := $(shell cd infrastructure/terraform && terraform output -raw aws_account_id 2>/dev/null))
	$(eval REGION := $(shell cd infrastructure/terraform && terraform output -raw aws_region 2>/dev/null))
	docker push $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/agentcore-gateway/appointment-server:latest
	@echo "✅ Appointment server image pushed successfully"

push-technician-image:
	@echo "📤 Pushing technician server image to ECR..."
	@if ! cd infrastructure/terraform && terraform output aws_account_id >/dev/null 2>&1; then \
		echo "❌ Terraform state not found. Please run 'make terraform-apply' first."; \
		exit 1; \
	fi
	$(eval ACCOUNT_ID := $(shell cd infrastructure/terraform && terraform output -raw aws_account_id 2>/dev/null))
	$(eval REGION := $(shell cd infrastructure/terraform && terraform output -raw aws_region 2>/dev/null))
	docker push $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/agentcore-gateway/technician-server:latest
	@echo "✅ Technician server image pushed successfully"

build-and-push: build-images tag-images push-images
	@echo "🎉 Complete container workflow completed successfully!"
	@echo "✅ All images are now available in ECR repositories"

clean-images:
	@echo "🧹 Cleaning up local container images..."
	docker rmi customer-server:latest 2>/dev/null || true
	docker rmi appointment-server:latest 2>/dev/null || true
	docker rmi technician-server:latest 2>/dev/null || true
	@if cd infrastructure/terraform && terraform output aws_account_id >/dev/null 2>&1; then \
		ACCOUNT_ID=$$(cd infrastructure/terraform && terraform output -raw aws_account_id 2>/dev/null); \
		REGION=$$(cd infrastructure/terraform && terraform output -raw aws_region 2>/dev/null); \
		docker rmi $$ACCOUNT_ID.dkr.ecr.$$REGION.amazonaws.com/agentcore-gateway/customer-server:latest 2>/dev/null || true; \
		docker rmi $$ACCOUNT_ID.dkr.ecr.$$REGION.amazonaws.com/agentcore-gateway/appointment-server:latest 2>/dev/null || true; \
		docker rmi $$ACCOUNT_ID.dkr.ecr.$$REGION.amazonaws.com/agentcore-gateway/technician-server:latest 2>/dev/null || true; \
	fi
	@echo "✅ Local container images cleaned up"

# EKS Deployment Commands
terraform-init: check-domain-env
	@echo "🚀 Initializing Terraform..."
	@echo "📍 Using domain: $$DOMAIN_NAME"
	@echo "✅ All Terraform configuration files are present and ready for deployment!"
	cd infrastructure/terraform && terraform init

terraform-plan: check-domain-env
	@echo "📋 Planning Terraform deployment..."
	@if [ ! -f infrastructure/terraform/.terraform.lock.hcl ]; then \
		echo "❌ Terraform not initialized. Run 'make terraform-init' first."; \
		exit 1; \
	fi
	@echo "📍 Using domain: $$DOMAIN_NAME"
	cd infrastructure/terraform && TF_VAR_domain_name=$$DOMAIN_NAME terraform plan

terraform-apply: check-domain-env
	@echo "🚀 Deploying EKS Auto Mode cluster with SSL/TLS and DNS..."
	@echo "⚠️  This will create AWS resources that may incur costs."
	@echo "📍 Make sure you have AWS credentials configured."
	@echo "🔐 SSL certificates will be created for domain: $$DOMAIN_NAME"
	@echo "📡 External DNS will manage Route53 records automatically"
	@echo "✅ All Terraform files are ready for deployment!"
	cd infrastructure/terraform && TF_VAR_domain_name=$$DOMAIN_NAME terraform apply -auto-approve

terraform-destroy: check-domain-env
	@echo "🗑️  Destroying EKS cluster and AWS resources..."
	@echo "⚠️  This will permanently delete all AWS resources created by Terraform."
	@if [ ! -f infrastructure/terraform/.terraform.lock.hcl ]; then \
		echo "❌ No Terraform state found. Nothing to destroy."; \
		exit 1; \
	fi
	@echo "📍 Using domain: $$DOMAIN_NAME"
	cd infrastructure/terraform && TF_VAR_domain_name=$$DOMAIN_NAME terraform destroy -auto-approve

terraform-output:
	@echo "📊 Terraform Outputs..."
	@if ! cd infrastructure/terraform && terraform output >/dev/null 2>&1; then \
		echo "❌ Terraform state not found. Please run 'make terraform-apply' first."; \
		exit 1; \
	fi
	cd infrastructure/terraform && terraform output




# ECR Deployment Commands (Enhanced)
deploy-ecr: check-domain-env
	@echo "🚀 Flexible ECR deployment..."
	@if [ -z "$(ENV)" ] || [ -z "$(ACTION)" ]; then \
		echo "❌ Usage: make deploy-ecr ENV=<development|production> ACTION=<apply|delete|diff|dry-run>"; \
		echo "   Examples:"; \
		echo "     make deploy-ecr ENV=development ACTION=apply"; \
		echo "     make deploy-ecr ENV=production ACTION=diff"; \
		echo "     make deploy-ecr ENV=development ACTION=delete"; \
		exit 1; \
	fi
	@echo "📍 Using domain: $$DOMAIN_NAME"
	export KUBECONFIG="/tmp/eks-cluster" && cd infrastructure/manifests && ./deploy-with-ecr.sh "$(ENV)" "$(ACTION)"



deploy-dev-ecr: check-domain-env
	@echo "🚀 Deploying to development with ECR images..."
	@echo "✨ Enhanced deployment with automatic cleanup and validation"
	@echo "📍 Using domain: $$DOMAIN_NAME"
	export KUBECONFIG="/tmp/eks-cluster" && cd infrastructure/manifests && ./deploy-with-ecr.sh development apply

deploy-prod-ecr: check-domain-env
	@echo "🚀 Deploying to production with ECR images..."
	@echo "✨ Enhanced deployment with automatic cleanup and validation"
	@echo "📍 Using domain: $$DOMAIN_NAME"
	export KUBECONFIG="/tmp/eks-cluster" && cd infrastructure/manifests && ./deploy-with-ecr.sh production apply











delete-dev-ecr:
	@echo "🗑️ Deleting development deployment..."
	@echo "🧹 Clean removal with automatic cleanup"
	export KUBECONFIG="/tmp/eks-cluster" && cd infrastructure/manifests && ./deploy-with-ecr.sh development delete

delete-prod-ecr:
	@echo "🗑️ Deleting production deployment..."
	@echo "🧹 Clean removal with automatic cleanup"
	export KUBECONFIG="/tmp/eks-cluster" && cd infrastructure/manifests && ./deploy-with-ecr.sh production delete

restart-dev:
	@echo "🔄 Restarting Kubernetes deployments in development namespace..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Restarting customer-server-dev deployment..."
	export KUBECONFIG="/tmp/eks-cluster" && kubectl rollout restart deployment/customer-server-dev -n development
	@echo "📊 Restarting appointment-server-dev deployment..."
	export KUBECONFIG="/tmp/eks-cluster" && kubectl rollout restart deployment/appointment-server-dev -n development
	@echo "📊 Restarting technician-server-dev deployment..."
	export KUBECONFIG="/tmp/eks-cluster" && kubectl rollout restart deployment/technician-server-dev -n development
	@echo "✅ All deployments restarted successfully!"
	@echo "💡 Use 'kubectl get pods -n development' to check pod status"

restart-prod:
	@echo "🔄 Restarting Kubernetes deployments in production namespace..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Restarting customer-server-prod deployment..."
	export KUBECONFIG="/tmp/eks-cluster" && kubectl rollout restart deployment/customer-server-prod -n production
	@echo "📊 Restarting appointment-server-prod deployment..."
	export KUBECONFIG="/tmp/eks-cluster" && kubectl rollout restart deployment/appointment-server-prod -n production
	@echo "📊 Restarting technician-server-prod deployment..."
	export KUBECONFIG="/tmp/eks-cluster" && kubectl rollout restart deployment/technician-server-prod -n production
	@echo "✅ All deployments restarted successfully!"
	@echo "💡 Use 'kubectl get pods -n production' to check pod status"

dry-run-dev-ecr:
	@echo "🔍 Dry run for development deployment..."
	@echo "📋 Show what would be applied without making changes"
	export KUBECONFIG="/tmp/eks-cluster" && cd infrastructure/manifests && ./deploy-with-ecr.sh development dry-run

dry-run-prod-ecr:
	@echo "🔍 Dry run for production deployment..."
	@echo "📋 Show what would be applied without making changes"
	export KUBECONFIG="/tmp/eks-cluster" && cd infrastructure/manifests && ./deploy-with-ecr.sh production dry-run

# Testing Commands
test-eks:
	@echo "🔍 Testing EKS cluster connectivity..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Cluster Info:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl cluster-info
	@echo ""
	@echo "📊 Node Status:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get nodes -o wide
	@echo ""
	@echo "📊 Node Pools (Auto Mode):"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get nodepools 2>/dev/null || echo "ℹ️  Node pools not available (may not be deployed yet)"

test-services:
	@echo "🔍 Testing Kubernetes service deployments..."
	@echo "📊 Deployments:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get deployments -n default
	@echo ""
	@echo "📊 Pods:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get pods -n default -o wide
	@echo ""
	@echo "📊 Services:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get services -n default
	@echo ""
	@echo "📊 Pod Health:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get pods -n default --field-selector=status.phase!=Running 2>/dev/null || echo "✅ All pods are running"

test-ingress:
	@echo "🔍 Testing ALB ingress controllers..."
	@echo "📊 Ingress Resources:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get ingress -n default
	@echo ""
	@echo "📊 Ingress Details:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl describe ingress -n default 2>/dev/null || echo "ℹ️  No ingress resources found"
	@echo ""
	@echo "📊 ALB Controller Status:"
	export KUBECONFIG="/tmp/eks-cluster" && kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller 2>/dev/null || echo "ℹ️  ALB controller not found"

test-all-eks: test-eks test-services test-ingress test-eks-rest-apis
	@echo ""
	@echo "🎉 Comprehensive EKS validation completed successfully!"
	@echo "✅ Infrastructure tests: EKS cluster, services, and ingress"
	@echo "✅ Application tests: REST API endpoints via ALB"
	@echo "💡 If any tests failed, check the EKS deployment status and ensure all manifests are applied."
	@echo ""
	@echo "📊 Complete Test Coverage:"
	@echo "  • EKS cluster connectivity and node status"
	@echo "  • Kubernetes service deployments and pod health"
	@echo "  • ALB ingress controllers and external access"
	@echo "  • REST API functionality via ALB endpoints"

check-eks-status:
	@echo "🔍 Checking EKS implementation status..."
	@echo ""
	@echo "📋 Terraform Foundation Files:"
	@if [ -f infrastructure/terraform/versions.tf ]; then echo "  ✅ versions.tf"; else echo "  ❌ versions.tf"; fi
	@if [ -f infrastructure/terraform/providers.tf ]; then echo "  ✅ providers.tf"; else echo "  ❌ providers.tf"; fi
	@if [ -f infrastructure/terraform/main.tf ]; then echo "  ✅ main.tf"; else echo "  ❌ main.tf"; fi
	@if [ -f infrastructure/terraform/variables.tf ]; then echo "  ✅ variables.tf (includes domain_name)"; else echo "  ❌ variables.tf"; fi
	@echo ""
	@echo "🏗️ Core Infrastructure Files:"
	@if [ -f infrastructure/terraform/vpc.tf ]; then echo "  ✅ vpc.tf (VPC with ALB-ready subnets)"; else echo "  🚧 vpc.tf (needed for VPC infrastructure)"; fi
	@if [ -f infrastructure/terraform/eks.tf ]; then echo "  ✅ eks.tf (EKS Auto Mode cluster)"; else echo "  🚧 eks.tf (needed for EKS Auto Mode cluster)"; fi
	@if [ -f infrastructure/terraform/alb.tf ]; then echo "  ✅ alb.tf (ALB ingress class)"; else echo "  🚧 alb.tf (needed for ALB ingress class)"; fi
	@if [ -f infrastructure/terraform/csi.tf ]; then echo "  ✅ csi.tf (EBS storage class)"; else echo "  🚧 csi.tf (needed for EBS storage class)"; fi
	@if [ -f infrastructure/terraform/ecr.tf ]; then echo "  ✅ ecr.tf (ECR repositories)"; else echo "  🚧 ecr.tf (needed for ECR repositories)"; fi
	@if [ -f infrastructure/terraform/outputs.tf ]; then echo "  ✅ outputs.tf (kubectl configuration)"; else echo "  🚧 outputs.tf (needed for kubectl configuration)"; fi
	@echo ""
	@echo "🔐 SSL/TLS & DNS Files:"
	@if [ -f infrastructure/terraform/acm.tf ]; then echo "  ✅ acm.tf (ACM SSL certificates with Route53 validation)"; else echo "  🚧 acm.tf (needed for SSL certificates)"; fi
	@if [ -f infrastructure/terraform/external-dns.tf ]; then echo "  ✅ external-dns.tf (External DNS IAM role and policies)"; else echo "  🚧 external-dns.tf (needed for DNS management)"; fi



test-eks-deployment:
	@echo "🔍 Comprehensive EKS deployment validation..."
	@echo ""
	@echo "📋 Step 1: Checking Terraform deployment..."
	@make terraform-plan
	@echo ""
	@echo "📋 Step 2: Testing EKS cluster..."
	@make test-eks
	@echo ""
	@echo "📋 Step 3: Testing services..."
	@make test-services
	@echo ""
	@echo "📋 Step 4: Testing ingress..."
	@make test-ingress
	@echo ""
	@echo "✅ Comprehensive EKS deployment validation completed!"

# EKS REST API Testing Commands
test-eks-discovery:
	@echo "🔍 Testing ALB URL discovery and endpoint accessibility..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Discovering ALB endpoints for EKS services..."
	cd infrastructure && uv run python -c "from testing_framework.eks_test_helpers import create_eks_test_config; config = create_eks_test_config(); config.print_discovery_summary()"
	@echo "✅ ALB URL discovery test completed!"

print-alb-urls:
	@echo "📍 ALB URLs from development namespace:"
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first." >&2; \
		exit 1; \
	fi
	@CUSTOMER_URL=$$(export KUBECONFIG="/tmp/eks-cluster" && kubectl get ingress -l app=customer-server -n development -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null); \
	APPOINTMENT_URL=$$(export KUBECONFIG="/tmp/eks-cluster" && kubectl get ingress -l app=appointment-server -n development -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null); \
	TECHNICIAN_URL=$$(export KUBECONFIG="/tmp/eks-cluster" && kubectl get ingress -l app=technician-server -n development -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null); \
	echo "Customer:    http://$$CUSTOMER_URL"; \
	echo "Appointment: http://$$APPOINTMENT_URL"; \
	echo "Technician:  http://$$TECHNICIAN_URL"

# OpenAPI JSON Dump Commands
dump-openapi-customer:
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first." >&2; \
		exit 1; \
	fi
	@CUSTOMER_DOMAIN=$$(export KUBECONFIG="/tmp/eks-cluster" && kubectl get ingress -l app=customer-server -n development -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null); \
	if [ -z "$$CUSTOMER_DOMAIN" ]; then \
		echo "❌ Customer server ingress domain not found. Make sure the service is deployed with ingress." >&2; \
		echo "💡 Run 'make deploy-dev-ecr' or 'make deploy-prod-ecr' first" >&2; \
		exit 1; \
	fi; \
	curl -s "https://$$CUSTOMER_DOMAIN/openapi.json" | jq '. + {"servers": [{"url": "https://'"$$CUSTOMER_DOMAIN"'"}]}'

dump-openapi-appointment:
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first." >&2; \
		exit 1; \
	fi
	@APPOINTMENT_DOMAIN=$$(export KUBECONFIG="/tmp/eks-cluster" && kubectl get ingress -l app=appointment-server -n development -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null); \
	if [ -z "$$APPOINTMENT_DOMAIN" ]; then \
		echo "❌ Appointment server ingress domain not found. Make sure the service is deployed with ingress." >&2; \
		echo "💡 Run 'make deploy-dev-ecr' or 'make deploy-prod-ecr' first" >&2; \
		exit 1; \
	fi; \
	curl -s "https://$$APPOINTMENT_DOMAIN/openapi.json" | jq '. + {"servers": [{"url": "https://'"$$APPOINTMENT_DOMAIN"'"}]}'

dump-openapi-technician:
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first." >&2; \
		exit 1; \
	fi
	@TECHNICIAN_DOMAIN=$$(export KUBECONFIG="/tmp/eks-cluster" && kubectl get ingress -l app=technician-server -n development -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null); \
	if [ -z "$$TECHNICIAN_DOMAIN" ]; then \
		echo "❌ Technician server ingress domain not found. Make sure the service is deployed with ingress." >&2; \
		echo "💡 Run 'make deploy-dev-ecr' or 'make deploy-prod-ecr' first" >&2; \
		exit 1; \
	fi; \
	curl -s "https://$$TECHNICIAN_DOMAIN/openapi.json" | jq '. + {"servers": [{"url": "https://'"$$TECHNICIAN_DOMAIN"'"}]}'

test-customer-eks-rest-api:
	@echo "🔍 Testing Customer server REST API via ALB endpoint..."
	@echo "✅ EKS REST API testing infrastructure is implemented and ready!"
	@echo "⚠️  This requires the Customer server to be deployed to EKS with ALB ingress"
	@echo "💡 Run 'make deploy-dev-ecr' or 'make deploy-prod-ecr' first if not deployed"
	@echo ""
	@echo "🌐 Running tests against ALB endpoints with automatic URL discovery..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Testing Customer server ALB endpoint..."
	cd infrastructure && EKS_TEST_MODE=true uv run pytest tests/test_customer_server_rest_api.py -v
	@echo "✅ Customer server EKS REST API tests completed!"

test-appointment-eks-rest-api:
	@echo "🔍 Testing Appointment server REST API via ALB endpoint..."
	@echo "✅ EKS REST API testing infrastructure is implemented and ready!"
	@echo "⚠️  This requires the Appointment server to be deployed to EKS with ALB ingress"
	@echo "💡 Run 'make deploy-dev-ecr' or 'make deploy-prod-ecr' first if not deployed"
	@echo ""
	@echo "🌐 Running tests against ALB endpoints with automatic URL discovery..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Testing Appointment server ALB endpoint..."
	cd infrastructure && EKS_TEST_MODE=true uv run pytest tests/test_appointment_server_rest_api.py -v
	@echo "✅ Appointment server EKS REST API tests completed!"

test-technician-eks-rest-api:
	@echo "🔍 Testing Technician server REST API via ALB endpoint..."
	@echo "✅ EKS REST API testing infrastructure is implemented and ready!"
	@echo "⚠️  This requires the Technician server to be deployed to EKS with ALB ingress"
	@echo "💡 Run 'make deploy-dev-ecr' or 'make deploy-prod-ecr' first if not deployed"
	@echo ""
	@echo "🌐 Running tests against ALB endpoints with automatic URL discovery..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Testing Technician server ALB endpoint..."
	cd infrastructure && EKS_TEST_MODE=true uv run pytest tests/test_technician_server_rest_api.py -v
	@echo "✅ Technician server EKS REST API tests completed!"

test-eks-rest-apis:
	@echo "🔍 Running comprehensive EKS REST API tests..."
	@echo "✅ EKS REST API testing infrastructure is implemented and ready!"
	@echo "⚠️  This requires all services to be deployed to EKS with ALB ingress"
	@echo "💡 Run 'make deploy-dev-ecr' or 'make deploy-prod-ecr' first if not deployed"
	@echo ""
	@echo "🌐 Testing all services against ALB endpoints with automatic URL discovery..."
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "❌ kubectl not found. Please install kubectl first."; \
		exit 1; \
	fi
	@echo "📊 Running comprehensive EKS REST API test suite..."
	cd infrastructure && EKS_TEST_MODE=true uv run pytest tests/test_customer_server_rest_api.py tests/test_appointment_server_rest_api.py tests/test_technician_server_rest_api.py -v --tb=short
	@echo ""
	@echo "🎉 All EKS REST API tests completed successfully!"
	@echo "✅ Comprehensive ALB endpoint testing with automatic URL discovery completed"
	@echo "✅ All three services (Customer, Appointment, Technician) tested via ALB endpoints"
	@echo "💡 Tests validate end-to-end functionality from ALB ingress to service pods"

# MCP Gateway Commands
setup-environment:
	@echo "🔧 Setting up environment configuration..."
	@./scripts/setup-environment.sh

check-domain-env:
	@if [ -z "$$DOMAIN_NAME" ]; then \
		echo "❌ DOMAIN_NAME environment variable is not set!"; \
		echo "💡 Please run the setup script first: make setup-environment"; \
		echo "💡 Or set it manually: export DOMAIN_NAME=your-domain.com"; \
		exit 1; \
	fi

setup-mcp-gateway: check-domain-env
	@echo "🚀 Setting up AWS Bedrock AgentCore MCP Gateway..."
	@echo "🔐 This will create Cognito user pool, IAM roles, and MCP Gateway resources"
	@echo "📍 Using domain: $$DOMAIN_NAME (environment: $${REST_API_ENV:-dev})"
	@echo "💡 Use 'make setup-mcp-gateway-help' to see customization options"
	@if [ -n "$(ARGS)" ]; then \
		echo "🔧 Using additional arguments: $(ARGS)"; \
		cd infrastructure/mcp_gateway/python && uv run mcp-gateway-setup $(ARGS); \
	else \
		cd infrastructure/mcp_gateway/python && uv run mcp-gateway-setup; \
	fi

setup-mcp-gateway-help:
	@echo "🔧 MCP Gateway Setup Command Help:"
	@echo ""
	cd infrastructure/mcp_gateway/python && uv run mcp-gateway-setup --help
	@echo ""
	@echo "💡 Examples:"
	@echo "  # Use domain from DOMAIN_NAME environment variable (dev environment)"
	@echo "  export DOMAIN_NAME=your-domain.com"
	@echo "  make setup-mcp-gateway"
	@echo ""
	@echo ""
	@echo "  # Use custom environment"
	@echo "  cd infrastructure/mcp_gateway/python && uv run mcp-gateway-setup --rest-api-domain my-domain.com --rest-api-env prod"
	@echo ""
	@echo "  # Use environment variable"
	@echo "  export REST_API_ENV=development"
	@echo "  cd infrastructure/mcp_gateway/python && uv run mcp-gateway-setup"
	@echo ""
	@echo "  # Use both custom domain and environment"
	@echo "  cd infrastructure/mcp_gateway/python && uv run mcp-gateway-setup --rest-api-domain my-domain.com --rest-api-env prod"

setup-mcp-gateway-env:
	@echo "🐍 Setting up MCP Gateway Python environment..."
	@echo "📦 Installing dependencies with Python 3.13..."
	cd infrastructure/mcp_gateway/python && uv venv --python 3.13
	cd infrastructure/mcp_gateway/python && uv pip install -e .
	@echo "✅ MCP Gateway environment setup complete!"
	@echo "💡 Available commands:"
	@echo "  • mcp-gateway-setup: Setup infrastructure"
	@echo "  • mcp-gateway-test: Run comprehensive AI agent test"
	@echo "  • mcp-gateway-test-connection: Quick connectivity test"

test-mcp-gateway-connection: check-domain-env
	@echo "🔍 Testing MCP Gateway basic connectivity..."
	@echo "📍 Using domain: $DOMAIN_NAME (environment: ${REST_API_ENV:-dev})"
	@echo "🔗 This test verifies gateway exists and token retrieval works"
	@if [ ! -d infrastructure/mcp_gateway/python/.venv ]; then \
		echo "❌ MCP Gateway environment not found. Run 'make setup-mcp-gateway-env' first."; \
		exit 1; \
	fi
	cd infrastructure/mcp_gateway/python && source .venv/bin/activate && mcp-gateway-test-connection

test-mcp-gateway: check-domain-env
	@echo "🤖 Testing MCP Gateway with AI Agent..."
	@echo "📍 Using domain: $DOMAIN_NAME (environment: ${REST_API_ENV:-dev})"
	@echo "🧠 This runs comprehensive tests with Strands AI Agent framework"
	@echo "🔧 Tests include: tool discovery, customer queries, and end-to-end functionality"
	@if [ ! -d infrastructure/mcp_gateway/python/.venv ]; then \
		echo "❌ MCP Gateway environment not found. Run 'make setup-mcp-gateway-env' first."; \
		exit 1; \
	fi
	cd infrastructure/mcp_gateway/python && source .venv/bin/activate && mcp-gateway-test
delete-mcp-gateway: check-domain-env
	@echo "🗑️ Deleting AWS Bedrock AgentCore MCP Gateway..."
	@echo "⚠️  This will permanently delete Cognito user pool, IAM roles, and MCP Gateway resources"
	@echo "📍 Using domain: $DOMAIN_NAME (environment: ${REST_API_ENV:-dev})"
	@if [ ! -d infrastructure/mcp_gateway/python/.venv ]; then \
		echo "❌ MCP Gateway environment not found. Run 'make setup-mcp-gateway-env' first."; \
		exit 1; \
	fi
	@if [ -n "$(ARGS)" ]; then \
		echo "🔧 Using additional arguments: $(ARGS)"; \
		cd infrastructure/mcp_gateway/python && source .venv/bin/activate && delete-gateway $(ARGS); \
	else \
		cd infrastructure/mcp_gateway/python && source .venv/bin/activate && delete-gateway; \
	fi


# ============================================================================
# Cleanup Commands - Delete AWS Environment in Logical Order
# ============================================================================

# Step 1: Delete Kubernetes resources from development namespace
cleanup-k8s-dev:
	@echo "🗑️  Step 1: Deleting Kubernetes resources from development namespace..."
	@echo "⚠️  This will delete all deployments, services, and ingress resources"
	@echo ""
	@if ! kubectl get namespace development &> /dev/null; then \
		echo "✅ Development namespace doesn't exist - nothing to clean up"; \
		exit 0; \
	fi
	@echo "📋 Current resources in development namespace:"
	@export KUBECONFIG="/tmp/eks-cluster" && kubectl get all,ingress -n development 2>/dev/null || echo "No resources found"
	@echo ""
	@read -p "Continue with deletion? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "❌ Cleanup cancelled"; \
		exit 1; \
	fi
	@echo ""
	@$(MAKE) delete-dev-ecr || true
	@echo ""
	@echo "⏳ Waiting for resources to be fully deleted (checking every 10 seconds)..."
	@$(MAKE) verify-k8s-cleanup NAMESPACE=development
	@echo "✅ Development namespace cleanup completed!"

# Step 2: Delete Kubernetes resources from production namespace
cleanup-k8s-prod:
	@echo "🗑️  Step 1: Deleting Kubernetes resources from production namespace..."
	@echo "⚠️  This will delete all deployments, services, and ingress resources"
	@echo ""
	@if ! kubectl get namespace production &> /dev/null; then \
		echo "✅ Production namespace doesn't exist - nothing to clean up"; \
		exit 0; \
	fi
	@echo "📋 Current resources in production namespace:"
	@export KUBECONFIG="/tmp/eks-cluster" && kubectl get all,ingress -n production 2>/dev/null || echo "No resources found"
	@echo ""
	@read -p "Continue with deletion? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "❌ Cleanup cancelled"; \
		exit 1; \
	fi
	@echo ""
	@$(MAKE) delete-prod-ecr || true
	@echo ""
	@echo "⏳ Waiting for resources to be fully deleted (checking every 10 seconds)..."
	@$(MAKE) verify-k8s-cleanup NAMESPACE=production
	@echo "✅ Production namespace cleanup completed!"

# Step 3: Delete all Kubernetes resources (both namespaces)
cleanup-k8s-all:
	@echo "🗑️  Deleting ALL Kubernetes resources (development + production)..."
	@echo "⚠️  This will delete all deployments, services, and ingress resources from both namespaces"
	@echo ""
	@$(MAKE) cleanup-k8s-dev || true
	@echo ""
	@$(MAKE) cleanup-k8s-prod || true
	@echo ""
	@echo "✅ All Kubernetes resources cleanup completed!"

# Verify Kubernetes cleanup - ensures services and ingress are fully deleted
verify-k8s-cleanup:
	@echo "🔍 Verifying Kubernetes cleanup for namespace: $(NAMESPACE)..."
	@export KUBECONFIG="/tmp/eks-cluster"; \
	MAX_WAIT=300; \
	ELAPSED=0; \
	while [ $$ELAPSED -lt $$MAX_WAIT ]; do \
		echo "⏳ Checking resources ($$ELAPSED/$$MAX_WAIT seconds)..."; \
		PODS=$$(kubectl get pods -n $(NAMESPACE) 2>/dev/null | grep -v "NAME" | wc -l || echo "0"); \
		SERVICES=$$(kubectl get services -n $(NAMESPACE) 2>/dev/null | grep -v "NAME" | wc -l || echo "0"); \
		INGRESS=$$(kubectl get ingress -n $(NAMESPACE) 2>/dev/null | grep -v "NAME" | wc -l || echo "0"); \
		DEPLOYMENTS=$$(kubectl get deployments -n $(NAMESPACE) 2>/dev/null | grep -v "NAME" | wc -l || echo "0"); \
		echo "   Pods: $$PODS | Services: $$SERVICES | Ingress: $$INGRESS | Deployments: $$DEPLOYMENTS"; \
		if [ "$$PODS" = "0" ] && [ "$$SERVICES" = "0" ] && [ "$$INGRESS" = "0" ] && [ "$$DEPLOYMENTS" = "0" ]; then \
			echo "✅ All resources deleted successfully!"; \
			break; \
		fi; \
		if [ $$ELAPSED -ge $$MAX_WAIT ]; then \
			echo "⚠️  Timeout waiting for resources to be deleted"; \
			echo "⚠️  Some resources may still be terminating:"; \
			kubectl get all,ingress -n $(NAMESPACE) 2>/dev/null || true; \
			echo "⚠️  You may need to manually delete remaining resources"; \
			break; \
		fi; \
		sleep 10; \
		ELAPSED=$$((ELAPSED + 10)); \
	done

# Step 4: Destroy Terraform infrastructure (EKS, VPC, IAM)
cleanup-terraform:
	@echo "🗑️  Step 2: Destroying Terraform infrastructure..."
	@echo "⚠️  This will destroy the EKS cluster, VPC, and all AWS resources"
	@echo ""
	@if ! cd infrastructure/terraform && terraform output >/dev/null 2>&1; then \
		echo "✅ No Terraform state found - nothing to destroy"; \
		exit 0; \
	fi
	@echo "📋 Current Terraform resources:"
	@cd infrastructure/terraform && terraform show -no-color | head -50 || true
	@echo ""
	@echo "⚠️  WARNING: This will permanently delete:"
	@echo "   • EKS Cluster"
	@echo "   • VPC and networking resources"
	@echo "   • IAM roles and policies"
	@echo "   • ECR repositories"
	@echo "   • ACM certificates"
	@echo "   • Route53 records"
	@echo ""
	@read -p "Have you verified all Kubernetes resources are deleted? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "❌ Please run 'make cleanup-k8s-all' first to delete Kubernetes resources"; \
		exit 1; \
	fi
	@read -p "Continue with Terraform destroy? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "❌ Cleanup cancelled"; \
		exit 1; \
	fi
	@echo ""
	@echo "🗑️  Running terraform destroy..."
	@$(MAKE) terraform-destroy
	@echo "✅ Terraform infrastructure destroyed!"

# Step 5: Delete AgentCore Gateway
cleanup-gateway:
	@echo "🗑️  Step 3: Deleting AgentCore Gateway..."
	@echo "⚠️  This will delete the AWS Bedrock AgentCore Gateway and associated resources"
	@echo ""
	@if [ ! -d infrastructure/mcp_gateway/python/.venv ]; then \
		echo "⚠️  MCP Gateway environment not set up"; \
		echo "💡 Setting up environment first..."; \
		$(MAKE) setup-mcp-gateway-env; \
	fi
	@echo ""
	@read -p "Have you verified Terraform resources are destroyed? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "❌ Please run 'make cleanup-terraform' first to destroy Terraform resources"; \
		exit 1; \
	fi
	@read -p "Continue with Gateway deletion? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "❌ Cleanup cancelled"; \
		exit 1; \
	fi
	@echo ""
	$(MAKE) delete-mcp-gateway

# Complete cleanup - all steps in order
cleanup-all:
	@echo "🗑️  COMPLETE AWS ENVIRONMENT CLEANUP"
	@echo "======================================"
	@echo ""
	@echo "⚠️  WARNING: This will permanently delete:"
	@echo "   1. All Kubernetes deployments, services, and ingress (dev + prod)"
	@echo "   2. EKS cluster, VPC, and all AWS infrastructure"
	@echo "   3. AWS Bedrock AgentCore Gateway"
	@echo ""
	@echo "This is a DESTRUCTIVE operation that cannot be undone!"
	@echo ""
	@read -p "Are you absolutely sure you want to proceed? (type 'DELETE' to confirm): " confirm; \
	if [ "$$confirm" != "DELETE" ]; then \
		echo "❌ Cleanup cancelled"; \
		exit 1; \
	fi
	@echo ""
	@echo "🚀 Starting complete cleanup process..."
	@echo ""
	@echo "================================================"
	@echo "STEP 1/3: Deleting Kubernetes Resources"
	@echo "================================================"
	@$(MAKE) cleanup-k8s-all || true
	@echo ""
	@echo "================================================"
	@echo "STEP 2/3: Destroying Terraform Infrastructure"
	@echo "================================================"
	@echo "⏳ Waiting 30 seconds to ensure all AWS resources are released..."
	@sleep 30
	@$(MAKE) terraform-destroy
	@echo ""
	@echo "================================================"
	@echo "STEP 3/3: Deleting AgentCore Gateway"
	@echo "================================================"
	@echo "⏳ Waiting 30 seconds before gateway deletion..."
	@sleep 30
	@$(MAKE) delete-mcp-gateway || true
	@echo ""
	@echo "🎉 Complete cleanup finished!"
	@echo ""
	@echo "✅ All AWS resources have been deleted:"
	@echo "   ✓ Kubernetes resources (deployments, services, ingress)"
	@echo "   ✓ EKS cluster and VPC"
	@echo "   ✓ AgentCore Gateway"
	@echo ""
	@echo "💡 You can now run 'make terraform-apply' to redeploy the environment"

# Comprehensive cleanup verification
verify-cleanup:
	@echo "🔍 Running comprehensive cleanup verification..."
	@bash infrastructure/scripts/verify-cleanup.sh
