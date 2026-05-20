variable "project_name"        { type = string }
variable "vpc_id"              { type = string }
variable "private_subnet_ids"  { type = list(string) }
variable "aws_region"          { type = string }
variable "riot_api_key" {
  type      = string
  sensitive = true
}
variable "db_password" { 
    type = string
    sensitive = true 
}
variable "db_endpoint"         { type = string }
variable "db_name"             { type = string }
