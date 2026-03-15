#!/bin/bash
echo "Creating Terraform state bucket..."
BUCKET_NAME="ai-rag-assistant-terraform-state-$(date +%s)"
aws s3 mb "s3://${BUCKET_NAME}" --region us-east-1
aws s3api put-bucket-versioning --bucket "${BUCKET_NAME}" --versioning-configuration Status=Enabled
echo "Created bucket: ${BUCKET_NAME}"
echo "Use this for TERRAFORM_STATE_BUCKET secret: ${BUCKET_NAME}"
