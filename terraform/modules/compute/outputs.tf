output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Paste this into your browser to reach the app"
}

output "ec2_security_group_id" {
  value       = aws_security_group.ec2.id
  description = "Passed to the database module for SG chaining"
}