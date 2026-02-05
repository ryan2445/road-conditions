#!/bin/bash
set -e

# Build the frontend
npm run build

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="road-analysis-reports-${ACCOUNT_ID}"

# Sync built assets to S3, excluding data files that Lambda manages, and set Cache-Control metadata
aws s3 sync dist/ "s3://${BUCKET}/" \
  --exclude "data.json" \
  --exclude "images/*" \
  --delete \
  --cache-control "public, max-age=0, s-maxage=3600, must-revalidate"

echo "Frontend deploy complete!"
