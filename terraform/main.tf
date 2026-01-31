terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

resource "aws_ecr_repository" "snow_on_road" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_permissions" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.reports.arn}/*"
      }
    ]
  })
}

# S3 bucket for HTML reports
resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-reports-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_website_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "reports" {
  bucket = aws_s3_bucket.reports.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.reports.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.reports]
}

resource "aws_lambda_function" "snow_on_road" {
  function_name = var.project_name
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.snow_on_road.repository_url}:latest"
  architectures = ["arm64"]
  timeout       = 300
  memory_size   = 4096

  environment {
    variables = {
      PYTHONUNBUFFERED = "1"
      S3_BUCKET        = aws_s3_bucket.reports.id
    }
  }

  depends_on = [aws_ecr_repository.snow_on_road]
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}"
  retention_in_days = 14
}

# EventBridge Rule - 9am PST (5pm UTC, or 4pm UTC during daylight saving)
# Using America/Los_Angeles timezone via cron expression
# 0 17 * * ? * = 9am PST (when PST is UTC-8)
# Note: AWS EventBridge uses UTC, so 9am PST = 5pm UTC
resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name                = "${var.project_name}-daily-9am-pst"
  description         = "Trigger snow-on-road check at 9am PST daily"
  schedule_expression = "cron(0 17 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "snow-on-road-daily"
  arn       = aws_lambda_function.snow_on_road.arn
  input     = jsonencode({ action = "email" })
}

resource "aws_lambda_permission" "allow_eventbridge_daily" {
  statement_id  = "AllowEventBridgeInvokeDaily"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.snow_on_road.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule.arn
}

# Hourly schedule to update HTML report
resource "aws_cloudwatch_event_rule" "hourly_schedule" {
  name                = "${var.project_name}-hourly"
  description         = "Update HTML report hourly"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "hourly_target" {
  rule      = aws_cloudwatch_event_rule.hourly_schedule.name
  target_id = "snow-on-road-hourly"
  arn       = aws_lambda_function.snow_on_road.arn
  input     = jsonencode({ action = "html_only" })
}

resource "aws_lambda_permission" "allow_eventbridge_hourly" {
  statement_id  = "AllowEventBridgeInvokeHourly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.snow_on_road.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_schedule.arn
}
