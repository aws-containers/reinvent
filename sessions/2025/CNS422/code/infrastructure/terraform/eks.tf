################################################################################
# EKS Auto Mode Cluster
################################################################################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.3"

  name                   = local.name
  kubernetes_version     = var.kubernetes_version
  endpoint_public_access = true

  # Enable cluster creator admin permissions
  enable_cluster_creator_admin_permissions = true

  # EKS Auto Mode configuration
  compute_config = {
    enabled    = true
    node_pools = local.node_pools
  }
  addons = {
    metrics-server = {}
    external-dns = {
      most_recent                 = true
      resolve_conflicts_on_update = "OVERWRITE"
      pod_identity_association = [{
        role_arn        = aws_iam_role.external_dns.arn
        service_account = "external-dns"
      }]
    }
  }

  # VPC configuration
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  tags = local.tags
}
