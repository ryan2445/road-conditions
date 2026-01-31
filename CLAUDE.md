# CLAUDE.md

## Project Overview

This project uses OpenAI's CLIP model to analyze Nevada DOT traffic camera images and classify road conditions (plowed, clear, dry). It runs as an AWS Lambda function triggered hourly and daily at 9am PST, sending results via SES email and publishing to an S3 bucket.

## Commands

```bash
# Install dependencies
uv sync
# Run locally
uv run python main.py

# Build Docker image
DOCKER_BUILDKIT=1 docker build --platform linux/arm64 --provenance=false -t road-analysis .

# Deploy infrastructure
cd terraform && terraform init && terraform apply

# Build and push to ECR (after terraform creates repo)
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com
docker tag road-analysis:latest <account>.dkr.ecr.us-west-2.amazonaws.com/road-analysis:latest
docker push <account>.dkr.ecr.us-west-2.amazonaws.com/road-analysis:latest
```

## Architecture

- `road_analysis.py` - Core logic: loads CLIP model, fetches camera images from nvroads.com, runs inference
- `main.py` - CLI entry point for local testing
- `lambda_handler.py` - AWS Lambda handler that runs check and sends SES email
- `templates/` - Jinja2 HTML templates for email and web page reports
- `cameras.json` - Camera IDs and names grouped by route
- `terraform/` - AWS infrastructure: ECR, Lambda, EventBridge schedule, IAM roles

The Lambda is packaged as a Docker container using the AWS Lambda Python 3.14 base image with uv for dependency management.
