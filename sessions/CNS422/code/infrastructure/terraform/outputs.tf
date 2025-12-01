################################################################################
# Terraform Outputs
################################################################################

output "configure_kubectl" {
  description = "Configure kubectl: make sure you're logged in with the correct AWS profile and run the following command to update your kubeconfig"
  value       = <<-EOT
    export KUBECONFIG="/tmp/${module.eks.cluster_name}"
    aws eks --region ${local.region} update-kubeconfig --name ${module.eks.cluster_name}
  EOT
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_arn" {
  description = "The Amazon Resource Name (ARN) of the cluster"
  value       = module.eks.cluster_arn
}

output "cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = module.eks.cluster_version
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "vpc_id" {
  description = "ID of the VPC where the cluster and its nodes will be provisioned"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

################################################################################
# ECR Repository Outputs
################################################################################

output "customer_server_ecr_repository_url" {
  description = "URL of the ECR repository for customer server"
  value       = aws_ecr_repository.customer_server.repository_url
}

output "appointment_server_ecr_repository_url" {
  description = "URL of the ECR repository for appointment server"
  value       = aws_ecr_repository.appointment_server.repository_url
}

output "technician_server_ecr_repository_url" {
  description = "URL of the ECR repository for technician server"
  value       = aws_ecr_repository.technician_server.repository_url
}

output "ecr_registry_id" {
  description = "The registry ID where the repositories were created"
  value       = aws_ecr_repository.customer_server.registry_id
}

################################################################################
# External DNS Outputs
################################################################################

output "external_dns_role_arn" {
  description = "ARN of the IAM role for External DNS"
  value       = aws_iam_role.external_dns.arn
}

output "external_dns_role_name" {
  description = "Name of the IAM role for External DNS"
  value       = aws_iam_role.external_dns.name
}

################################################################################
# ACM Certificate Outputs
################################################################################

output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate_validation.main.certificate_arn
}

output "acm_certificate_domain_name" {
  description = "Domain name of the ACM certificate"
  value       = aws_acm_certificate.main.domain_name
}

output "acm_certificate_subject_alternative_names" {
  description = "Subject alternative names of the ACM certificate"
  value       = aws_acm_certificate.main.subject_alternative_names
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID for the domain"
  value       = data.aws_route53_zone.main.zone_id
}

output "route53_zone_name" {
  description = "Route53 hosted zone name"
  value       = data.aws_route53_zone.main.name
}

################################################################################
# AWS Account and Region Outputs
################################################################################

output "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS region"
  value       = local.region
}


