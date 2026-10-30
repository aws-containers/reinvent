terraform {
  required_version = ">= 1.13"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.13"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.38"
    }
  }
}
