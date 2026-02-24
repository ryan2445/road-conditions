data "onepassword_item" "google_api_key" {
  count = var.google_api_key == "" ? 1 : 0
  vault = var.op_vault
  title = "Google API Key"
}

data "onepassword_item" "openai_api_key" {
  count = var.openai_api_key == "" ? 1 : 0
  vault = var.op_vault
  title = "OpenAI API Key"
}

data "onepassword_item" "anthropic_api_key" {
  count = var.anthropic_api_key == "" ? 1 : 0
  vault = var.op_vault
  title = "Anthropic API Key"
}

locals {
  google_api_key    = var.google_api_key != "" ? var.google_api_key : data.onepassword_item.google_api_key[0].password
  openai_api_key    = var.openai_api_key != "" ? var.openai_api_key : data.onepassword_item.openai_api_key[0].password
  anthropic_api_key = var.anthropic_api_key != "" ? var.anthropic_api_key : data.onepassword_item.anthropic_api_key[0].password
}
