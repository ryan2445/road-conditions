# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project fetches and compiles Nevada DOT traffic camera images. It runs as an AWS Lambda function triggered hourly, sending results via SES email (at 9am PST) and publishing to an S3 bucket served by CloudFront.

## Commands

### Backend (Python)

```bash
cd backend
uv sync                    # Install dependencies
uv run python main.py      # Run locally (tests mt_rose route only)
```

### Frontend (Svelte)

```bash
cd frontend
npm install                # Install dependencies
npm run dev                # Development server (proxies data to production)
npm run build              # Build production assets
npm run check              # TypeScript/Svelte type checking
npm run lint               # ESLint
npm run format             # Prettier
```

### Docker/Deploy

```bash
# Build and deploy everything (backend + frontend)
./deploy.sh

# Or manually:
DOCKER_BUILDKIT=1 docker build --platform linux/arm64 --provenance=false -t road-analysis backend

# Infrastructure
cd terraform && terraform init && terraform apply
```

## Architecture

### Backend (inside `backend/`)

- `backend/service.py` - Orchestration: runs camera image fetching across groups, returns `GroupedResults`
- `backend/models.py` - Shared types (`CameraConfig`, `CameraResult`)
- `backend/config.py` - Configuration: loads `cameras.json`
- `backend/camera_sources.py` - Fetches HLS video frames from Nevada DOT streams via PyAV
- `backend/reporting.py` - Text and HTML report formatting, Jinja2 email template rendering
- `backend/publishing.py` - AWS integration: SES email sending, S3 upload of data.json + images, CloudFront invalidation
- `backend/main.py` - CLI entry point for local testing
- `backend/lambda_handler.py` - AWS Lambda handler that runs check, sends SES email (only at 9am PST/17:00 UTC), and uploads to S3
- `backend/cameras.json` - Camera IDs, names, and HLS stream URLs grouped by route

### Frontend

Svelte 5 app (uses `$state()` runes) served via CloudFront at `road-conditions.ryanh.click`:

- `frontend/src/App.svelte` - Main component, fetches `/data.json` and renders camera grid
- `frontend/src/lib/components/` - CameraCard, Header components
- `frontend/src/lib/api.ts` - API layer for fetching road conditions
- `frontend/src/lib/types.ts` - TypeScript interfaces (`CameraData`, `CameraGroup`, `RoadConditionsData`)

Dev server proxies `/data.json` and `/images/` to production CloudFront URL.

### Infrastructure (Terraform)

- Lambda (ARM64, 1GB RAM, 300s timeout) with ECR container image
- EventBridge hourly schedule
- S3 bucket (private) + CloudFront with Origin Access Control
- SES for email delivery

### Data Flow

1. EventBridge triggers Lambda hourly
2. Lambda fetches HLS frames from Nevada DOT streams via PyAV
3. Results uploaded to S3 as `data.json` + `images/{id}.jpg` (1-hour cache)
4. Email sent via SES at 9am PST only
5. Frontend fetches data.json from CloudFront CDN
