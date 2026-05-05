output "bucket_name" {
  description = "S3 bucket holding the rendered docs site"
  value       = aws_s3_bucket.site.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (used by deploy workflow for cache invalidation)"
  value       = aws_cloudfront_distribution.site.id
}

output "cloudfront_url" {
  description = "Public URL of the docs hub. Add this as the Embed web part target on the SharePoint hub page."
  value       = "https://${aws_cloudfront_distribution.site.domain_name}"
}

output "deploy_role_arn" {
  description = "IAM role ARN that GitHub Actions assumes for deploys. Set this as the AWS_DEPLOY_ROLE_ARN repo variable."
  value       = aws_iam_role.deploy.arn
}
