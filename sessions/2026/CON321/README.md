# CON321 — Build a production multi-tier application on Amazon ECS

**AWS re:Invent 2026** · Workshop · 300 - Advanced

Real applications have frontends, APIs, workers, and databases that all need to communicate reliably. In this workshop, build a complete multi-tier containerized architecture on Amazon ECS from scratch. Configure service-to-service networking with Service Connect, implement per-tier autoscaling policies, deploy updates with automated rollback, and observe your application using CloudWatch Container Insights. Walk away with a working architecture you can use as a reference for your own workloads. Bring your laptop to participate.

## Workshop topics
1. **Deploy an MVP on Amazon ECS**: create a cluster, register a task definition, run the store's UI as a Fargate service, and ship a change with a rolling update. Learn more: [Clusters](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/clusters.html), [Task definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html), [Rolling update deployments](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html)
2. **Deploy the Multi-Tier Application**: split the store into UI, Catalog, Orders, and Checkout services that communicate through ECS Service Connect, review its metrics and automatic retries, and open a shell in a running container with ECS Exec. Learn more: [Service Connect](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect.html), [ECS Exec](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html)
3. **Handling traffic surges**: add Service Auto Scaling with a target tracking policy, then run a load test and watch the UI service scale out and back in. Learn more: [Service Auto Scaling](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html), [Target tracking scaling](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-autoscaling-targettracking.html)
4. **Zero downtime deployments**: release a new UI version with native ECS blue/green deployments behind an Application Load Balancer, and validate it before it receives production traffic. Learn more: [Blue/green deployments](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-blue-green.html), [Deployment lifecycle hooks](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-lifecycle-hooks.html)
5. **Scale ingress with Amazon ECS Gateway**: create a shared gateway once and connect the UI service to it, so the service gets its own HTTPS URL and certificate without a new load balancer. Learn more: [Amazon ECS Gateway](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/gateway-overview.html)
6. **(Optional) Monitor your application**: use CloudWatch Container Insights with enhanced observability and CloudWatch Logs to go from service-level metrics down to individual tasks and containers. Learn more: [Container Insights](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cloudwatch-container-insights.html)

## Get hands-on
- [AWS Workshops (awsworkshop.io)](https://awsworkshop.io/?trk=a12002ed-20e7-4b73-b4af-5bac900f1cec&sc_channel=el) — hands-on workshops from AWS and AWS Partners

## Amazon ECS resources
- [Amazon ECS product page](https://aws.amazon.com/ecs/)
- [Amazon ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
- [Amazon ECS best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-best-practices.html)
- [ECS Workshop](https://ecsworkshop.com/)
- [AWS Fargate product page](https://aws.amazon.com/fargate/)
- [Amazon ECS Blueprints](https://github.com/aws-ia/ecs-blueprints) — infrastructure as code examples to start your own ECS projects

## Blog posts
- [New – Amazon ECS Service Connect Enabling Easy Communication Between Microservices](https://aws.amazon.com/blogs/aws/new-amazon-ecs-service-connect-enabling-easy-communication-between-microservices/)
- [Encrypt Amazon ECS traffic: VPC encryption controls and Service Connect TLS](https://aws.amazon.com/blogs/containers/encrypt-amazon-ecs-traffic-vpc-encryption-controls-and-service-connect-tls/)
- [NEW – Using Amazon ECS Exec to access your containers on AWS Fargate and Amazon EC2](https://aws.amazon.com/blogs/containers/new-using-amazon-ecs-exec-access-your-containers-fargate-ec2/)
- [Amazon ECS introduces new high-resolution metrics for faster service auto scaling](https://aws.amazon.com/blogs/aws/amazon-ecs-introduces-new-high-resolution-metrics-for-faster-service-auto-scaling/)
- [Deep dive: Auto scaling response times on Amazon ECS](https://aws.amazon.com/blogs/containers/deep-dive-auto-scaling-response-times-on-amazon-ecs/)
- [Accelerate safe software releases with new built-in blue/green deployments in Amazon ECS](https://aws.amazon.com/blogs/aws/accelerate-safe-software-releases-with-new-built-in-blue-green-deployments-in-amazon-ecs/)
- [Extending deployment pipelines with Amazon ECS blue green deployments and lifecycle hooks](https://aws.amazon.com/blogs/containers/extending-deployment-pipelines-with-amazon-ecs-blue-green-deployments-and-lifecycle-hooks/)
- [Streamline service-to-service communication during deployments with Amazon ECS Service Connect](https://aws.amazon.com/blogs/containers/streamline-service-to-service-communication-during-deployments-with-amazon-ecs-service-connect/)
- [Introducing Amazon ECS Gateway: A fully-managed ingress solution for ECS services](https://aws.amazon.com/blogs/aws/introducing-amazon-ecs-gateway-a-fully-managed-ingress-solution-for-ecs-services/)
- [Container Insights with enhanced observability now available in Amazon ECS](https://aws.amazon.com/blogs/aws/container-insights-with-enhanced-observability-now-available-in-amazon-ecs/)

## More from AWS Containers
- [AWS Containers blog](https://aws.amazon.com/blogs/containers/)
- [AWS Containers public roadmap](https://github.com/aws/containers-roadmap)
- [Containers from the Couch](https://www.youtube.com/containersfromthecouch) — videos and live streams from the AWS Containers team

## Session materials
- Slides: _added after the event_
- Code samples: _added by the speakers_
