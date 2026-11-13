#!/bin/bash
set -e

aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 079958958349.dkr.ecr.us-west-2.amazonaws.com

DOCKER_BUILDKIT=1 docker build --platform linux/arm64 --provenance=false -t road-conditions backend

docker tag road-conditions:latest 079958958349.dkr.ecr.us-west-2.amazonaws.com/road-conditions:latest

docker push 079958958349.dkr.ecr.us-west-2.amazonaws.com/road-conditions:latest

cd ./frontend && ./deploy.sh && cd ..

aws lambda update-function-code --function-name road-conditions --image-uri 079958958349.dkr.ecr.us-west-2.amazonaws.com/road-conditions:latest

aws lambda wait function-updated --function-name road-conditions

aws lambda invoke --function-name road-conditions --invocation-type Event /dev/null

echo "Deploy complete!"
