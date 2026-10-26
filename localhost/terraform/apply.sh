#!/bin/bash
# The state is kept between runs so "docker compose up" can run again on a configured Keycloak.
# When Keycloak starts from scratch, Terraform notices the objects are gone and creates them again.
set -e

terraform init -input=false
terraform apply -input=false --auto-approve
