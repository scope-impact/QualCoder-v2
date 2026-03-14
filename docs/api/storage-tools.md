# Storage MCP Tools API

Tools for managing S3 data stores and DVC-versioned file transfers.

## configure_datastore

Configure an S3 bucket as the project's data store with DVC remote.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bucket_name` | string | Yes | S3 bucket name (3-63 chars, lowercase, hyphens/dots) |
| `region` | string | Yes | AWS region (e.g., `us-east-1`) |
| `prefix` | string | No | S3 key prefix. Default: `""` |
| `dvc_remote_name` | string | No | DVC remote name. Default: `"origin"` |

**Response:**

```json
{
  "store_id": "01j...",
  "bucket_name": "research-data",
  "region": "us-east-1",
  "prefix": "",
  "dvc_remote_name": "origin"
}
```

---

## scan_datastore

List files in the configured S3 data store.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `prefix` | string | No | S3 key prefix filter. Default: store prefix |

**Response:**

```json
{
  "file_count": 3,
  "files": [
    {
      "key": "raw/interview_001.txt",
      "size_bytes": 2048,
      "last_modified": "2026-03-14T10:00:00Z",
      "extension": ".txt"
    }
  ]
}
```

---

## pull_source

Pull a file from S3 to local project via DVC.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | Yes | S3 object key |
| `local_path` | string | Yes | Local filesystem path for the file |

**Response:**

```json
{
  "key": "raw/interview_001.txt",
  "local_path": "/project/sources/interview_001.txt"
}
```

---

## push_results

Push a local file to S3 via DVC.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `local_path` | string | Yes | Path to local file |
| `destination_key` | string | Yes | S3 key for the uploaded file |

**Response:**

```json
{
  "destination_key": "exports/codebook_v1.txt",
  "local_path": "/project/exports/codebook.txt"
}
```

---

## export_and_push

Export project data and push to S3. Supports formats: `qdpx`, `codebook`, `sqlite`, `html`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `export_format` | string | Yes | One of: `qdpx`, `codebook`, `sqlite`, `html` |
| `destination_key` | string | Yes | S3 key for the exported file |

**Response:**

```json
{
  "export_format": "qdpx",
  "destination_key": "exports/project.qdpx",
  "local_path": "/tmp/staging/export.qdpx"
}
```

---

## scan_and_import

Pull a file from S3 and auto-import based on extension.

Supported formats: `.qdpx`, `.rqda`, `.csv`, `.txt`, `.db`, `.sqlite`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | Yes | S3 object key of file to import |

**Response:**

```json
{
  "key": "raw/data.csv",
  "result": "Import successful"
}
```

---

## Domain Events

Storage operations publish these events via the EventBus:

| Event | Type String | When |
|-------|-------------|------|
| `StoreConfigured` | `storage.store_configured` | Store configured successfully |
| `StoreScanned` | `storage.store_scanned` | Store scanned, files discovered |
| `FilePulled` | `storage.file_pulled` | File pulled from S3 |
| `ExportPushed` | `storage.export_pushed` | Export pushed to S3 |

## Error Codes

| Code | Description |
|------|-------------|
| `STORE_NOT_CONFIGURED/INVALID_BUCKET` | Bucket name violates S3 naming rules |
| `STORE_NOT_CONFIGURED/INVALID_REGION` | Region is empty |
| `STORE_NOT_SCANNED/NOT_CONFIGURED` | No store configured yet |
| `STORE_NOT_SCANNED/CONNECTION_FAILED` | S3 unreachable |
| `FILE_NOT_PULLED/NOT_CONFIGURED` | No store configured |
| `FILE_NOT_PULLED/INVALID_KEY` | Invalid S3 key |
| `FILE_NOT_PULLED/DOWNLOAD_FAILED` | Download error |
| `EXPORT_NOT_PUSHED/NOT_CONFIGURED` | No store configured |
| `EXPORT_NOT_PUSHED/INVALID_KEY` | Invalid destination key |
| `EXPORT_NOT_PUSHED/UPLOAD_FAILED` | Upload error |
