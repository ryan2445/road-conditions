resource "aws_acm_certificate" "cloudfront" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"
}

resource "aws_cloudfront_origin_access_control" "reports" {
  name                              = "${var.project_name}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "reports" {
  enabled             = true
  default_root_object = "index.html"
  aliases             = [var.domain_name]

  origin {
    domain_name              = aws_s3_bucket.reports.bucket_regional_domain_name
    origin_id                = aws_s3_bucket.reports.id
    origin_access_control_id = aws_cloudfront_origin_access_control.reports.id
  }

  default_cache_behavior {
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = aws_s3_bucket.reports.id
    viewer_protocol_policy = "redirect-to-https"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.cloudfront.arn
    ssl_support_method  = "sni-only"
  }
}
