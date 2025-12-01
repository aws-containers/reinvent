################################################################################
# EBS CSI Storage Class for EKS Auto Mode
################################################################################

resource "kubernetes_storage_class_v1" "ebs_csi" {
  depends_on = [module.eks]

  metadata {
    name = "auto-ebs-sc"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner = "ebs.csi.eks.amazonaws.com"
  volume_binding_mode = "WaitForFirstConsumer"

  parameters = {
    type      = "gp3"
    encrypted = "true"
  }
}
