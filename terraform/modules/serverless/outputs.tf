output "lambda_function_name" {
  value = aws_lambda_function.tft_fetcher.function_name
}

output "lambda_security_group_id" {
  value       = aws_security_group.lambda.id
  description = "Add this to RDS SG ingress to allow Lambda → RDS"
}