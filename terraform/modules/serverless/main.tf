resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Basic execution — lets Lambda write logs to CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC access — Lambda needs this to reach RDS in private subnets
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Custom policy — lets Lambda read secrets from Secrets Manager
resource "aws_iam_role_policy" "lambda_secrets" {
  name = "${var.project_name}-lambda-secrets-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.app_secrets.arn
    }]
  })
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}/app-secrets"
  description = "Riot API key and DB credentials"

  tags = {
    Name = "${var.project_name}-secrets"
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    riot_api_key  = var.riot_api_key
    db_password   = var.db_password
    db_endpoint   = var.db_endpoint
    db_name       = var.db_name
  })
}

resource "aws_security_group" "lambda" {
  name        = "${var.project_name}-lambda-sg"
  description = "Lambda function security group"
  vpc_id      = var.vpc_id

  # No inbound rules — Lambda is never called directly over the network
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-lambda-sg"
  }
}

resource "aws_lambda_function" "tft_fetcher" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  function_name    = "${var.project_name}-tft-fetcher"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.main"    # filename.function_name
  runtime          = "python3.11"
  timeout          = 300               # 5 minutes — Riot API can be slow
  memory_size      = 256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      SECRET_ARN = aws_secretsmanager_secret.app_secrets.arn
      AWS_REGION_NAME = var.aws_region
    }
  }

  tags = {
    Name = "${var.project_name}-tft-fetcher"
  }
}

# Packages your Python file into a zip for Lambda
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/functions/handler.py"
  output_path = "${path.module}/functions/handler.zip"
}

resource "aws_cloudwatch_event_rule" "weekly" {
  name                = "${var.project_name}-weekly-trigger"
  description         = "Trigger TFT leaderboard fetch every Sunday at midnight"
  schedule_expression = "cron(0 0 ? * SUN *)"   # AWS cron syntax

  tags = {
    Name = "${var.project_name}-weekly-trigger"
  }
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.weekly.name
  target_id = "TFTFetcherLambda"
  arn       = aws_lambda_function.tft_fetcher.arn
}

# Grants EventBridge permission to invoke Lambda
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tft_fetcher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly.arn
}