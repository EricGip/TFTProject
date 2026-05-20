variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "ec2_security_group_id" {
  type        = string
  description = "EC2 SG ID — only this SG can reach RDS"
}

variable "db_password" {
  type      = string
  sensitive = true
}