################################################################################
# ECR Repositories for REST API Servers
################################################################################

# ECR repositories for each REST API server
resource "aws_ecr_repository" "appointment_server" {
  name                 = "agentcore-gateway/appointment-server"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_repository" "customer_server" {
  name                 = "agentcore-gateway/customer-server"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

resource "aws_ecr_repository" "technician_server" {
  name                 = "agentcore-gateway/technician-server"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}
