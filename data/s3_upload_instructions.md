# S3 Upload Instructions

This document provides instructions for uploading product images to S3 and updating the product catalog with S3 image URLs.

## Prerequisites

1. AWS CLI must be installed and configured with appropriate credentials.
2. The S3 bucket must exist and be accessible with the configured credentials.
3. Product images must be generated and available in the `data/images` directory.

## Step 1: Prepare S3 Upload Manifest

The first step is to prepare a manifest file for S3 upload. This file contains information about the product images to be uploaded, including file paths, sizes, and content types.

```bash
python scripts/s3/prepare_s3_upload.py --images-dir data/images --output-file data/s3_upload_manifest.json
```

This will create a manifest file at `data/s3_upload_manifest.json` with the following structure:

```json
{
  "timestamp": "2025-03-13T20:44:33.123456",
  "total_images": 100,
  "total_size_bytes": 10485760,
  "total_size_mb": 10.0,
  "images": [
    {
      "product_id": "PROD-000001",
      "file_path": "data/images/PROD-000001.jpg",
      "file_size": 102400,
      "content_type": "image/jpeg"
    },
    ...
  ]
}
```

## Step 2: Upload Images to S3

The next step is to upload the product images to S3 using the manifest file.

```bash
python scripts/s3/upload_to_s3.py --manifest-file data/s3_upload_manifest.json --bucket-name your-bucket-name --prefix products
```

Replace `your-bucket-name` with the name of your S3 bucket. The `--prefix` parameter is optional and specifies a prefix for the S3 keys.

This will upload the images to S3 and create a mapping file at `data/s3_url_mapping.json` with the following structure:

```json
{
  "timestamp": "2025-03-13T20:45:33.123456",
  "bucket_name": "your-bucket-name",
  "prefix": "products",
  "total_images": 100,
  "uploaded_images": 100,
  "failed_images": 0,
  "product_to_s3_url": {
    "PROD-000001": "https://your-bucket-name.s3.amazonaws.com/products/PROD-000001.jpg",
    ...
  }
}
```

## Step 3: Update Product Catalog with S3 URLs

The final step is to update the product catalog with the S3 image URLs.

```bash
python scripts/s3/update_catalog_with_s3_urls.py --catalog-file data/products.json --s3-url-mapping-file data/s3_url_mapping.json --output-file data/products_with_s3_urls.json
```

This will update the product catalog with the S3 image URLs and save it to `data/products_with_s3_urls.json`.

## Step 4: Ingest Updated Catalog into Elasticsearch

After updating the product catalog, you can ingest it into Elasticsearch using the Kafka-based ingestion pipeline.

```bash
python scripts/kafka/product_producer.py --products-file data/products_with_s3_urls.json
```

This will send the products to the Kafka topic, and the consumer will process them and ingest them into Elasticsearch.

## Troubleshooting

If you encounter any issues during the S3 upload process, check the following:

1. AWS CLI is installed and configured with appropriate credentials.
2. The S3 bucket exists and is accessible with the configured credentials.
3. Product images are generated and available in the specified directory.
4. The manifest file is correctly generated.
5. The S3 URL mapping file is correctly generated.
6. The product catalog is correctly updated with S3 image URLs.
