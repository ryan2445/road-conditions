# EventBridge Rule - 9am PST (5pm UTC, or 4pm UTC during daylight saving)
# Using America/Los_Angeles timezone via cron expression
# 0 17 * * ? * = 9am PST (when PST is UTC-8)
# Note: AWS EventBridge uses UTC, so 9am PST = 5pm UTC
resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name                = "${var.project_name}-daily-9am-pst"
  description         = "Trigger road-analysis check at 9am PST daily"
  schedule_expression = "cron(0 17 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "road-analysis-daily"
  arn       = aws_lambda_function.road_analysis.arn
  input     = jsonencode({ action = "email" })
}

resource "aws_lambda_permission" "allow_eventbridge_daily" {
  statement_id  = "AllowEventBridgeInvokeDaily"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.road_analysis.function_name
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
  target_id = "road-analysis-hourly"
  arn       = aws_lambda_function.road_analysis.arn
  input     = jsonencode({ action = "html_only" })
}

resource "aws_lambda_permission" "allow_eventbridge_hourly" {
  statement_id  = "AllowEventBridgeInvokeHourly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.road_analysis.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_schedule.arn
}
