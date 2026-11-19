# ECS Production Shield

A skill for Kiro and Claude Code. It reviews your Amazon ECS infrastructure code for 10 settings that prevent common production incidents, and shows you how to fix what's missing.

From the AWS re:Invent 2026 lightning talk CON341, "5 Amazon ECS features that prevent common production incidents".

> **Disclaimer:** Sample code from the AWS re:Invent 2026 session CON341. It is not a supported AWS product. It is provided as is, under the MIT-0 license, without warranty of any kind. Test and review every finding and every change against your organization's standards before you use it in production.

## What it checks

| # | Check | What to set |
|---|---|---|
| 01 | Circuit breaker | enable and rollback, minimumHealthyPercent 100 |
| 02 | Task health | startPeriod, grace period, essential: false on sidecars (log routers can stay essential) |
| 03 | Capacity providers | base on FARGATE, weight on FARGATE_SPOT |
| 04 | Service Connect | perRequestTimeoutSeconds that covers the slowest request |
| 05 | Deployment alarms | alarms with rollback, bake time longer than the alarm window |
| 06 | Graceful shutdown | stopTimeout up to 120 s, tuned deregistration delay |
| 07 | Immutable image tags | image digests or ECR IMMUTABLE tags |
| 08 | Auto scaling | target tracking, minimum of 2 tasks, no fixed desired count |
| 09 | Memory limits | memory hard limit on every container |
| 10 | Container order | dependsOn with condition HEALTHY |

It works with AWS CDK, Terraform, CloudFormation and similar tools. Your coding agent reads the code in whatever language it is written in.

## Install

**Kiro**

In the Kiro panel, open **Agent Steering & Skills**, click **+**, choose **Import a skill**, then **GitHub**, and paste:

```
https://github.com/aws-containers/reinvent/tree/main/sessions/2026/CON341/ecs-production-shield
```

Or, from the root of your project:

```bash
mkdir -p .kiro/skills/ecs-production-shield
curl -fsSL https://raw.githubusercontent.com/aws-containers/reinvent/main/sessions/2026/CON341/ecs-production-shield/SKILL.md -o .kiro/skills/ecs-production-shield/SKILL.md
```

**Claude Code**

From the root of your project:

```bash
mkdir -p .claude/skills/ecs-production-shield
curl -fsSL https://raw.githubusercontent.com/aws-containers/reinvent/main/sessions/2026/CON341/ecs-production-shield/SKILL.md -o .claude/skills/ecs-production-shield/SKILL.md
```

To use it in every project, put it in `~/.kiro/skills/` or `~/.claude/skills/` instead.

## Use

Ask your agent:

> Check my ECS service for production readiness.

Or run it directly with `/ecs-production-shield`.

It first asks a few things the code can't show, like how long your app takes to start. You get a report for each service, with the file and line of each finding, the fix in your code's language, and a link to the AWS documentation. After you apply fixes, it offers to log every change.

## What it does not do

- It does not change your files unless you say yes, and it shows every change.
- It does not deploy, call AWS APIs or need AWS credentials.
- It does not run your project's code or download anything unless you say yes to that exact command.
- It does not check logging, secrets, runtime hardening, ECS Exec or IAM roles in this version.

Review every change before you deploy it.

## Versions

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | Oct 30, 2026 | First version. |
| 1.1.0 | Nov 18, 2026 | Asks for the main container and the start, request and shutdown times before it checks. Warns when the Service Connect timeout is shorter than the slowest request. Judges values passed into modules. A missing container health check behind a load balancer is now a WARN, and `launchType` on Fargate is a hint. Start order is checked only when one container needs another. Version tags on mutable repositories now warn. Suggests a change log after fixes. |
| 1.2.0 | Nov 18, 2026 | Moved to the aws-containers/reinvent repo. A FireLens log router can stay essential, as AWS recommends, and a non-essential one needs monitoring. The Service Connect timeout is judged by the value in effect, set or default, against the slowest request. Warns when a fixed desired count can reset the count that auto scaling set. |
| 1.2.1 | Nov 19, 2026 | Review feedback. Validation commands such as `terraform init` and `cdk synth` run only after the user says yes, and module source is read only if it's already on disk. Text inside the reviewed repo is data, never instructions. |

## License

MIT-0. See https://spdx.org/licenses/MIT-0.html
