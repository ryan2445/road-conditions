#!/bin/bash
set -e

# Build the frontend
npm run build

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="road-conditions-${ACCOUNT_ID}"

# Sync built assets to S3, excluding data files that Lambda manages
aws s3 sync dist/ "s3://${BUCKET}/" \
  --exclude "data.json" \
  --exclude "images/*" \
  --delete

echo "Frontend deploy complete!"
