data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  # Do not include local zones
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  name            = var.cluster_name
  region          = var.region
  vpc_cidr        = var.vpc_cidr
  cluster_version = var.kubernetes_version
  node_pools      = var.node_pools

  # Domain name from environment variable (via TF_VAR_domain_name)
  domain_name = var.domain_name

  azs = slice(data.aws_availability_zones.available.names, 0, var.number_availability_zones)

  tags = {
    Blueprint = local.name
    Domain    = local.domain_name
  }
}


