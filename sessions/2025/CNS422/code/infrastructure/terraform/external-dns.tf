################################################################################
# External DNS IAM Role and Policy (Pod Identity Association)
################################################################################

data "aws_iam_policy_document" "external_dns_assume_role_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole", "sts:TagSession"]
  }
}

resource "aws_iam_role" "external_dns" {
  assume_role_policy = data.aws_iam_policy_document.external_dns_assume_role_policy.json
  name               = "${local.name}-external-dns"
  tags               = local.tags
}

data "aws_iam_policy_document" "external_dns" {
  statement {
    effect = "Allow"
    actions = [
      "route53:ChangeResourceRecordSets"
    ]
    resources = ["arn:aws:route53:::hostedzone/*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "route53:ListHostedZones",
      "route53:ListResourceRecordSets",
      "route53:ListTagsForResource"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "external_dns" {
  description = "External DNS policy for EKS cluster ${local.name}"
  name        = "${local.name}-external-dns"
  policy      = data.aws_iam_policy_document.external_dns.json
  tags        = local.tags
}

resource "aws_iam_role_policy_attachment" "external_dns" {
  policy_arn = aws_iam_policy.external_dns.arn
  role       = aws_iam_role.external_dns.name
}


