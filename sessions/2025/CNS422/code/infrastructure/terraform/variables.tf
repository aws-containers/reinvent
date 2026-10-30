variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "number_availability_zones" {
  description = "Number of availability zones"
  type        = number
  default     = 2
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "eks-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.33"
}

variable "node_pools" {
  description = "Node pools configuration"
  type        = list(string)
  default     = ["general-purpose", "system"]
}

variable "domain_name" {
  description = "Domain name for ACM certificate. Must be set via DOMAIN_NAME environment variable or terraform.tfvars"
  type        = string
  default     = null

  validation {
    condition     = var.domain_name != null && var.domain_name != ""
    error_message = "Domain name must be provided. Set via DOMAIN_NAME environment variable or terraform.tfvars file."
  }
}

