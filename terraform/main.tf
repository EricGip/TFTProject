module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
}

module "compute" {
  source = "./modules/compute"

  project_name       = var.project_name
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  ami_id             = var.ami_id
}

module "database" {
  source = "./modules/database"

  project_name          = var.project_name
  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  ec2_security_group_id = module.compute.ec2_security_group_id
  db_password           = var.db_password
}

module "serverless" {
  source = "./modules/serverless"
  project_name       = var.project_name
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  aws_region         = var.aws_region
  riot_api_key       = var.riot_api_key
  db_password        = var.db_password
  db_endpoint        = module.database.db_endpoint
  db_name            = module.database.db_name
}

resource "aws_security_group_rule" "rds_lambda_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = module.database.rds_security_group_id
  source_security_group_id = module.serverless.lambda_security_group_id
  description              = "Allow Lambda to write to RDS"
}

output "alb_dns_name" {
  description = "Load balancer URL — paste into browser to reach the app"
  value       = module.compute.alb_dns_name
}

output "db_endpoint" {
  description = "RDS endpoint for reference"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "lambda_function_name" {
  description = "Invoke this manually to test the Riot API fetch"
  value       = module.serverless.lambda_function_name
}


