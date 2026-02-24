variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "project_name" {
  type    = string
  default = "road-analysis"
}

variable "domain_name" {
  type    = string
  default = "road-conditions.ryanh.click"
}

variable "op_account" {
  type = string
}

variable "op_vault" {
  type = string
}

variable "google_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = "none"
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
  default   = "none"
}
