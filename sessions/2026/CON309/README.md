# CON309 - Connect your Amazon ECS services without the complexity

**AWS re:Invent 2026** | Chalk talk | 300 - Advanced

Connecting services on Amazon Elastic Container Service (Amazon ECS) gets harder as your platform grows. Each team builds its own ingress, and connections grow faster than services. Task IP addresses change all the time, and some callers run in other VPCs and accounts. Traffic between services also needs encryption. This chalk talk explored when to use Elastic Load Balancing, Amazon ECS Gateway, Amazon ECS Service Connect and Amazon VPC Lattice. It also covered how to combine them as your architecture grows. On the whiteboard, we worked through four challenges and your questions on one architecture.

The links below follow the options in the order the talk covered them.

## Elastic Load Balancing

- [Use load balancing to distribute Amazon ECS service traffic](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-load-balancing.html) - the load balancer types Amazon ECS supports
- [Use an Application Load Balancer for Amazon ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/alb.html) - path and host routing for HTTP and HTTPS services
- [Optimize load balancer health check parameters for Amazon ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/load-balancer-healthcheck.html) - faster deployments with tuned health checks

## Amazon ECS Gateway

- [Introducing Amazon ECS Gateway](https://aws.amazon.com/blogs/aws/introducing-amazon-ecs-gateway-a-fully-managed-ingress-solution-for-ecs-services) on the AWS News Blog
- [Amazon ECS Gateway](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/gateway-overview.html) - managed HTTPS ingress for Amazon ECS services
- [Create and manage an Amazon ECS Gateway](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/gateway-managing.html) - the platform team's side
- [Connect Amazon ECS services to a gateway](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/gateway-connect-service.html) - the application team's side

## Amazon ECS Service Connect

- [Amazon ECS Service Connect](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect.html) - short names, the proxy, retries and outlier detection
- [Amazon ECS Service Connect zone-aware routing](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-zone-aware-routing.html) - how the proxy keeps traffic in the same Availability Zone
- [Amazon ECS Service Connect access logs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-envoy-access-logs.html) - what the proxy logs for each request
- [Service Connect with shared AWS Cloud Map namespaces](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-shared-namespaces.html) - connect Amazon ECS services across AWS accounts
- [Announcing zone-aware routing in Amazon ECS Service Connect](https://aws.amazon.com/blogs/containers/announcing-zone-aware-routing-in-amazon-ecs-service-connect/)
- [Migrate existing Amazon ECS services from service discovery to Amazon ECS Service Connect](https://aws.amazon.com/blogs/containers/migrate-existing-amazon-ecs-services-from-service-discovery-to-amazon-ecs-service-connect/)
- [Encrypt Amazon ECS Service Connect traffic](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-tls.html) - how Service Connect uses AWS Private CA for TLS
- [Enabling TLS for Amazon ECS Service Connect](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/enable-service-connect-tls.html) - the steps for your own services
- [Understand AWS Private CA CA modes](https://docs.aws.amazon.com/privateca/latest/userguide/short-lived-certificates.html) - how the general-purpose and short-lived modes differ
- [Encrypt Amazon ECS traffic: VPC encryption controls and Service Connect TLS](https://aws.amazon.com/blogs/containers/encrypt-amazon-ecs-traffic-vpc-encryption-controls-and-service-connect-tls/)

## Amazon VPC Lattice

- [What is Amazon VPC Lattice?](https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html)
- [Target groups in VPC Lattice](https://docs.aws.amazon.com/vpc-lattice/latest/ug/target-groups.html) - the compute you register behind a VPC Lattice service
- [VPC Lattice auth policies](https://docs.aws.amazon.com/vpc-lattice/latest/ug/auth-policies.html) - control which callers can reach a service
- [Use Amazon VPC Lattice with Amazon ECS services](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-vpc-lattice.html) - register Amazon ECS services directly as VPC Lattice targets
- [Streamline container application networking with built-in Amazon ECS support in Amazon VPC Lattice](https://aws.amazon.com/blogs/aws/streamline-container-application-networking-with-native-amazon-ecs-support-in-amazon-vpc-lattice/)
- [Build secure application networks with VPC Lattice, Amazon ECS, and AWS Lambda](https://aws.amazon.com/blogs/containers/build-secure-application-networks-with-vpc-lattice-amazon-ecs-and-aws-lambda/)

## Get hands-on

- [Networking learning path in the Amazon ECS Immersion Day](https://catalog.workshops.aws/ecs-immersion-day/en-US/60-lp-networking) - try each option yourself in a self-paced lab in your own AWS account
- [AWS Workshops (awsworkshop.io)](https://awsworkshop.io/?trk=77e45d81-9500-433d-b632-c5396401a321&sc_channel=el) - hands-on workshops from AWS and AWS Partners

## Amazon ECS resources

- [Amazon ECS product page](https://aws.amazon.com/ecs/)
- [Amazon ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
- [Amazon ECS best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-best-practices.html)

## More from AWS Containers

- [AWS Containers blog](https://aws.amazon.com/blogs/containers/)
- [AWS Containers public roadmap](https://github.com/aws/containers-roadmap)
