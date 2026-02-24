# Hourly schedule to update HTML report / send email
resource "aws_cloudwatch_event_rule" "hourly_schedule" {
  name        = "${var.project_name}-hourly"
  description = "Update HTML report hourly (7am-7pm PST)"
  # PST = UTC-8; so 7am-7pm PST is 15:00-03:00 UTC
  schedule_expression = "cron(0 15-23,0-3 * * ? *)"
}

resource "aws_cloudwatch_event_target" "hourly_target" {
  rule = aws_cloudwatch_event_rule.hourly_schedule.name
  arn  = aws_lambda_function.road_analysis.arn
}

resource "aws_lambda_permission" "allow_eventbridge_hourly" {
  statement_id  = "AllowEventBridgeInvokeHourly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.road_analysis.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_schedule.arn
}
