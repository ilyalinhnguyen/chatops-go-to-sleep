# Version-Specific Rollback

This document provides detailed information about how to use the version-specific rollback feature in the ChatOps API.

## Overview

The version-specific rollback feature allows you to roll back a Kubernetes deployment to:

1. A specific revision by ID
2. A specific image
3. A specific version tag
4. The previous revision (default behavior)

## API Endpoint

```
POST /api/v1/kubernetes/service/rollback
```

## Request Options

### Option 1: Default Rollback (to previous revision)

If you don't specify a revision, the system will automatically roll back to the previous revision.

```json
{
  "namespace": "production",
  "name": "payment-service"
}
```

### Option 2: Rollback to Specific Revision ID

You can roll back to a specific revision by providing the revision ID. This can be the full ReplicaSet name or just the revision number.

```json
{
  "namespace": "production",
  "name": "payment-service",
  "revisionId": "payment-service-7d9c4b5f96"
}
```

Or using just the revision number:

```json
{
  "namespace": "production",
  "name": "payment-service",
  "revisionId": "3"
}
```

### Option 3: Rollback to Specific Image

You can roll back to a deployment that used a specific image:

```json
{
  "namespace": "production",
  "name": "payment-service",
  "revisionImage": "company/payment-service:v2.3.0"
}
```

### Option 4: Rollback to Specific Version

You can roll back to a specific version by providing just the version tag:

```json
{
  "namespace": "production",
  "name": "payment-service",
  "version": "v2.3.0"
}
```

## Example Usage

### Example 1: Default Rollback

```bash
curl -X POST \
  http://your-api-host:8000/api/v1/kubernetes/service/rollback \
  -H 'Authentication: your-api-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "namespace": "production",
    "name": "payment-service"
  }'
```

### Example 2: Rollback to Specific Revision ID

```bash
curl -X POST \
  http://your-api-host:8000/api/v1/kubernetes/service/rollback \
  -H 'Authentication: your-api-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "namespace": "production",
    "name": "payment-service",
    "revisionId": "payment-service-7d9c4b5f96"
  }'
```

### Example 3: Rollback to Specific Image

```bash
curl -X POST \
  http://your-api-host:8000/api/v1/kubernetes/service/rollback \
  -H 'Authentication: your-api-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "namespace": "production",
    "name": "payment-service",
    "revisionImage": "company/payment-service:v2.3.0"
  }'
```

### Example 4: Rollback to Specific Version

```bash
curl -X POST \
  http://your-api-host:8000/api/v1/kubernetes/service/rollback \
  -H 'Authentication: your-api-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "namespace": "production",
    "name": "payment-service",
    "version": "v2.3.0"
  }'
```

## Response

The API will return a success response when the rollback is initiated:

```json
{
  "status": "success",
  "message": "Service rolled back successfully",
  "data": {
    "name": "payment-service",
    "namespace": "production",
    "revisionId": "payment-service-7d9c4b5f96",
    "revisionImage": "",
    "version": ""
  }
}
```

## Error Handling

### No Revisions Found

```json
{
  "status": "error",
  "message": "Failed to rollback service",
  "error": "no revisions found for deployment payment-service"
}
```

### Specific Revision Not Found

```json
{
  "status": "error",
  "message": "Failed to rollback service",
  "error": "revision payment-service-7d9c4b5f96 not found for deployment payment-service"
}
```

### No Matching Image Found

```json
{
  "status": "error",
  "message": "Failed to rollback service",
  "error": "no revision found with image company/payment-service:v2.3.0 for deployment payment-service"
}
```

## Important Notes

1. You can only roll back to **existing** revisions in the deployment history
2. The revision history may be limited based on your Kubernetes configuration
3. You should only specify one of: `revisionId`, `revisionImage`, or `version`
4. When using `version`, the system searches for any image with a matching tag
5. The rollback operation is performed using a direct update, not the Kubernetes Rollback API
