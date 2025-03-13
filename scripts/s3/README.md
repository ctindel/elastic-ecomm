# S3 Upload Scripts

This directory contains scripts for uploading product images to S3 and updating the product catalog with S3 image URLs.

## Scripts

### 1. prepare_s3_upload.py

This script creates a manifest file for S3 upload.

```bash
python scripts/s3/prepare_s3_upload.py --images-dir data/images --output-file data/s3_upload_manifest.json
```

### 2. upload_to_s3.py

This script uploads product images to S3 using the AWS CLI.

```bash
python scripts/s3/upload_to_s3.py --manifest-file data/s3_upload_manifest.json --bucket-name your-bucket-name --prefix products
```

### 3. update_catalog_with_s3_urls.py

This script updates the product catalog with S3 image URLs.

```bash
python scripts/s3/update_catalog_with_s3_urls.py --catalog-file data/products.json --s3-url-mapping-file data/s3_url_mapping.json --output-file data/products_with_s3_urls.json
```

## Usage

1. Generate product images using the image generation scripts.
2. Prepare the S3 upload manifest.
3. Upload the images to S3.
4. Update the product catalog with S3 image URLs.
5. Ingest the updated catalog into Elasticsearch.

## Requirements

- AWS CLI must be installed and configured with appropriate credentials.
- The S3 bucket must exist and be accessible with the configured credentials.
- Product images must be generated and available in the specified directory.
