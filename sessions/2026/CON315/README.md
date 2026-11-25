# CON315 - Connect and secure service-to-service networking on Amazon ECS

**AWS re:Invent 2026** | Builders' session | 300 - Advanced

In this builders' session, you took a storefront on Amazon Elastic Container Service (Amazon ECS) from mock backends to real services. Amazon ECS Service Connect linked Catalog and Carts to the UI by name, and proxy retries kept the store serving through a failing task. Certificates from your own AWS Private Certificate Authority (AWS Private CA) then encrypted the traffic between services. Orders and Checkout run on Amazon EC2 in another VPC, and the UI now calls them through Amazon VPC Lattice. To finish, you opened the store on a managed HTTPS URL with Amazon ECS Gateway.

The links below follow the lab's chapters, so you can go deeper on the part you care about most.

## Connect services by name with Amazon ECS Service Connect

- [Amazon ECS Service Connect](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect.html) - short names, the proxy, retries and outlier detection
- [Amazon ECS Service Connect zone-aware routing](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-zone-aware-routing.html) - how the proxy keeps traffic in the same Availability Zone
- [Amazon ECS Service Connect access logs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-envoy-access-logs.html) - the proxy logs you read in the lab
- [Service Connect with shared AWS Cloud Map namespaces](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-shared-namespaces.html) - connect Amazon ECS services across AWS accounts
- [Amazon ECS Service Connect launch post](https://aws.amazon.com/blogs/aws/new-amazon-ecs-service-connect-enabling-easy-communication-between-microservices/) on the AWS News Blog
- [Announcing zone-aware routing in Amazon ECS Service Connect](https://aws.amazon.com/blogs/containers/announcing-zone-aware-routing-in-amazon-ecs-service-connect/)
- [Migrate existing Amazon ECS services from service discovery to Amazon ECS Service Connect](https://aws.amazon.com/blogs/containers/migrate-existing-amazon-ecs-services-from-service-discovery-to-amazon-ecs-service-connect/)

## Encrypt service-to-service traffic with AWS Private CA

- [Encrypt Amazon ECS Service Connect traffic](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-tls.html) - how Service Connect uses AWS Private CA for TLS
- [Enabling TLS for Amazon ECS Service Connect](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/enable-service-connect-tls.html) - the steps for your own services
- [Understand AWS Private CA CA modes](https://docs.aws.amazon.com/privateca/latest/userguide/short-lived-certificates.html) - the short-lived certificate mode the lab used
- [Encrypt Amazon ECS traffic: VPC encryption controls and Service Connect TLS](https://aws.amazon.com/blogs/containers/encrypt-amazon-ecs-traffic-vpc-encryption-controls-and-service-connect-tls/)

## Reach services in another VPC with Amazon VPC Lattice

- [What is Amazon VPC Lattice?](https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html)
- [Target groups in VPC Lattice](https://docs.aws.amazon.com/vpc-lattice/latest/ug/target-groups.html) - the Amazon EC2 targets behind Orders and Checkout
- [VPC Lattice auth policies](https://docs.aws.amazon.com/vpc-lattice/latest/ug/auth-policies.html) - the access control the lab left out
- [Use Amazon VPC Lattice with Amazon ECS services](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-vpc-lattice.html) - register Amazon ECS services directly as VPC Lattice targets
- [Streamline container application networking with built-in Amazon ECS support in Amazon VPC Lattice](https://aws.amazon.com/blogs/aws/streamline-container-application-networking-with-native-amazon-ecs-support-in-amazon-vpc-lattice/)
- [Build secure application networks with VPC Lattice, Amazon ECS, and AWS Lambda](https://aws.amazon.com/blogs/containers/build-secure-application-networks-with-vpc-lattice-amazon-ecs-and-aws-lambda/)

## Open services to customers with Amazon ECS Gateway

- [Amazon ECS Gateway](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/gateway-overview.html) - managed HTTPS ingress for Amazon ECS services
- [Create and manage an Amazon ECS Gateway](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/gateway-managing.html) - the platform team's side
- [Connect Amazon ECS services to a gateway](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/gateway-connect-service.html) - the application team's side
- [Introducing Amazon ECS Gateway](https://aws.amazon.com/blogs/aws/introducing-amazon-ecs-gateway-a-fully-managed-ingress-solution-for-ecs-services) on the AWS News Blog

## Get hands-on

- [Networking learning path in the Amazon ECS Immersion Day](https://catalog.workshops.aws/ecs-immersion-day/en-US/60-lp-networking) - a self-paced version of this lab that runs in your own AWS account
- [AWS Workshops (awsworkshop.io)](https://awsworkshop.io/?trk=4840ea1e-aff5-4d4e-ac25-23d2c58b6341&sc_channel=el) - hands-on workshops from AWS and AWS Partners

## Amazon ECS resources

- [Amazon ECS product page](https://aws.amazon.com/ecs/)
- [Amazon ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
- [Amazon ECS best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-best-practices.html)

## More from AWS Containers

- [AWS Containers blog](https://aws.amazon.com/blogs/containers/)
- [AWS Containers public roadmap](https://github.com/aws/containers-roadmap)
