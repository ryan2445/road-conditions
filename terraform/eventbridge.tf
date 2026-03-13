# Hourly schedule to update HTML report / send email (7am-7pm Pacific Time)
# Using EventBridge Scheduler to properly handle Daylight Savings Time
resource "aws_scheduler_schedule" "hourly_schedule" {
  name        = "${var.project_name}-hourly"
  description = "Update HTML report hourly (7am-7pm local time)"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 7-19 * * ? *)"
  schedule_expression_timezone = "America/Los_Angeles"

  target {
    arn      = aws_lambda_function.road_analysis.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

resource "aws_iam_role" "scheduler_role" {
  name = "${var.project_name}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name = "${var.project_name}-scheduler-invoke-lambda"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.road_analysis.arn
      }
    ]
  })
}
