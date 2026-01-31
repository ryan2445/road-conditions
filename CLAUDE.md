# CLAUDE.md

## Project Overview

Snow-on-road uses OpenAI's CLIP model to analyze Nevada DOT traffic camera images and classify road conditions (plowed, clear, dry). It runs as an AWS Lambda function triggered hourly and daily at 9am PST, sending results via SES email and publishing to an S3 bucket.

## Commands

```bash
# Install dependencies
uv sync
# Run locally
uv run python main.py

# Build Docker image
DOCKER_BUILDKIT=1 docker build --platform linux/arm64 --provenance=false -t snow-on-road .

# Deploy infrastructure
cd terraform && terraform init && terraform apply

# Build and push to ECR (after terraform creates repo)
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com
docker tag snow-on-road:latest <account>.dkr.ecr.us-west-2.amazonaws.com/snow-on-road:latest
docker push <account>.dkr.ecr.us-west-2.amazonaws.com/snow-on-road:latest
```

## Architecture

- `snow_checker.py` - Core logic: loads CLIP model, fetches camera images from nvroads.com, runs inference
- `main.py` - CLI entry point for local testing
- `lambda_handler.py` - AWS Lambda handler that runs check and sends SES email
- `templates/` - Jinja2 HTML templates for email and web page reports
- `cameras.json` - Camera IDs and names grouped by route
- `terraform/` - AWS infrastructure: ECR, Lambda, EventBridge schedule, IAM roles

The Lambda is packaged as a Docker container using the AWS Lambda Python 3.14 base image with uv for dependency management.
