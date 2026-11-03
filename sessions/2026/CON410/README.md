# CON410 — Deep dive into networking architectures for Amazon EKS Hybrid Nodes

**AWS re:Invent 2026** · Chalk Talk · 400 - Expert

Join this interactive chalk talk to explore hybrid networking design patterns for Amazon EKS Hybrid Nodes. We’ll cover different IPAM and routing strategies for hybrid pod networks, including Cilium BGP control-plane integration with your on-premises infrastructures. We’ll also explore various load balancing and Kubernetes services networking options for your hybrid nodes. Additionally, we’ll deep dive into the new Amazon EKS Hybrid Nodes gateway, demonstrating how it simplifies pod-to-pod communication, webhook connectivity, and AWS service integration across cloud and on-premises environments - without requiring changes to your existing network infrastructure.

## Get hands-on
- [AWS Workshops (awsworkshop.io)](https://awsworkshop.io/?trk=7890ceaf-1296-4ea1-b9d8-6757d9605b8d&sc_channel=el) — hands-on workshops from AWS and AWS Partners

## Amazon EKS resources
- [Amazon EKS product page](https://aws.amazon.com/eks/)
- [Amazon EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html)
- [Amazon EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/introduction.html)
- [EKS Workshop](https://www.eksworkshop.com/)

## More from AWS Containers
- [AWS Containers blog](https://aws.amazon.com/blogs/containers/)
- [AWS Containers public roadmap](https://github.com/aws/containers-roadmap)

## Session materials
- Slides: _added after the event_

Amazon EKS User Guide
- [Amazon EKS Hybrid Nodes overview](https://docs.aws.amazon.com/eks/latest/userguide/hybrid-nodes-overview.html)
- [Prepare networking for hybrid nodes](https://docs.aws.amazon.com/eks/latest/userguide/hybrid-nodes-networking.html)
- [Configure CNI for hybrid nodes](https://docs.aws.amazon.com/eks/latest/userguide/hybrid-nodes-cni.html)
- [Amazon EKS Hybrid Nodes gateway](https://docs.aws.amazon.com/eks/latest/userguide/hybrid-nodes-gateway-overview.html)

AWS Containers Blog
- [A deep dive into Amazon EKS Hybrid Nodes](https://aws.amazon.com/blogs/containers/a-deep-dive-into-amazon-eks-hybrid-nodes/)
- [Deep dive into cluster networking for Amazon EKS Hybrid Nodes](https://aws.amazon.com/blogs/containers/deep-dive-into-cluster-networking-for-amazon-eks-hybrid-nodes)
- [Simplify hybrid Kubernetes networking with Amazon EKS Hybrid Nodes gateway](https://aws.amazon.com/blogs/containers/simplify-hybrid-kubernetes-networking-with-amazon-eks-hybrid-nodes-gateway)
- [Deploy production generative AI at the edge using Amazon EKS Hybrid Nodes with NVIDIA DGX](https://aws.amazon.com/blogs/containers/deploy-production-generative-ai-at-the-edge-using-amazon-eks-hybrid-nodes-with-nvidia-dgx/)

AWS re:Post
- [Deploying Cilium Networking on Amazon EKS Hybrid Nodes](https://repost.aws/articles/ARpKAVyUXgSBW1h9GBhh2JKA/deploying-cilium-networking-on-amazon-eks-hybrid-nodes)

AWS Samples
- [EKS Hybrid Nodes proof-of-concept (PoC) template](https://github.com/aws-samples/sample-eks-hybrid-nodes-poc)

Amazon EKS Hybrid Nodes Gateway source code
- [EKS Hybrid Nodes gateway](https://github.com/aws/eks-hybrid-nodes-gateway)
