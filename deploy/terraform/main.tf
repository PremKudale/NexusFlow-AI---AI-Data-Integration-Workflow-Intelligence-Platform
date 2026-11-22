terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20.0"
    }
  }
}

variable "project_id" {
  type    = string
  default = "enterprise-intelligence-prod"
}

variable "region" {
  type    = string
  default = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Pub/Sub Topics
resource "google_pubsub_topic" "data_ingestion" {
  name = "data-ingestion"
}

resource "google_pubsub_topic" "workflow_execution" {
  name = "workflow-execution"
}

resource "google_pubsub_subscription" "workflow_sub" {
  name  = "workflow-execution-sub"
  topic = google_pubsub_topic.workflow_execution.id

  ack_deadline_seconds = 60
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

# 2. BigQuery Dataset & Tables
resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "enterprise_analytics"
  friendly_name               = "Enterprise Analytics Warehouse"
  location                    = "US"
  default_table_expiration_ms = null
}

resource "google_bigquery_table" "revenue_summary" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "quarterly_revenue_summary"

  schema = <<EOF
[
  {"name": "quarter", "type": "STRING", "mode": "REQUIRED"},
  {"name": "year", "type": "INTEGER", "mode": "REQUIRED"},
  {"name": "gross_revenue", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "cogs", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "operating_margin_pct", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "cloud_infrastructure_cost", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "hardware_deliveries_count", "type": "INTEGER", "mode": "NULLABLE"}
]
EOF
}

# 3. Artifact Registry for Cloud Run Containers
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "platform-repo"
  format        = "DOCKER"
}

