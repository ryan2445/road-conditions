#!/bin/bash
set -e

# Build the frontend
npm run build

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="road-analysis-reports-${ACCOUNT_ID}"

# Sync built assets to S3, excluding data files that Lambda manages
aws s3 sync dist/ "s3://${BUCKET}/" \
  --exclude "data.json" \
  --exclude "images/*" \
  --delete

# Get CloudFront distribution ID
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[?DomainName=='${BUCKET}.s3.us-west-2.amazonaws.com']].Id | [0]" \
  --output text)

if [ "$DISTRIBUTION_ID" != "None" ] && [ -n "$DISTRIBUTION_ID" ]; then
  echo "Invalidating CloudFront distribution ${DISTRIBUTION_ID}..."
  aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*"
else
  echo "Warning: Could not find CloudFront distribution"
fi

# Invoke lambda to update data
echo "Invoking Lambda to refresh data..."
aws lambda invoke --function-name road-analysis /dev/null

echo "Deploy complete!"
