output "db_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "RDS connection string for the Flask app"
}

output "db_name" {
  value = aws_db_instance.main.db_name
}

output "rds_security_group_id" {
  value = aws_security_group.rds.id
}