################################################################################
# ALB Ingress Class for EKS Auto Mode
################################################################################

resource "kubernetes_ingress_class_v1" "alb" {
  depends_on = [module.eks]

  metadata {
    name = "alb"
    labels = {
      "app.kubernetes.io/name" = "LoadBalancerController"
    }
  }

  spec {
    controller = "eks.amazonaws.com/alb"
  }
}
