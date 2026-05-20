variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Used to name/tag all resources"
  type        = string
  default     = "tft-dashboard"
}

variable "ami_id" {
  description = "Amazon Linux 2023 AMI for your region"
  type        = string
  # us-west-2: ami-00563078bca04e287 (al2023, 2026-05-15)
}

variable "db_password" {
  description = "RDS master password — never hardcode this"
  type        = string
  sensitive   = true  # Terraform won't print this in logs
}

variable "riot_api_key" {
  description = "Your Riot Games API key"
  type        = string
  sensitive   = true
}