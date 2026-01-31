output "ecr_repository_url" {
  value = aws_ecr_repository.road_analysis.repository_url
}

output "lambda_function_name" {
  value = aws_lambda_function.road_analysis.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.road_analysis.arn
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.lambda_logs.name
}

output "schedule_rule_arn" {
  value = aws_cloudwatch_event_rule.daily_schedule.arn
}

output "website_url" {
  value = aws_s3_bucket_website_configuration.reports.website_endpoint
}
