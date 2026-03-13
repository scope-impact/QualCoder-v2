"""
Storage Context: S3 Scanner Unit Tests (TDD RED phase)

Uses moto to mock S3 — no real AWS calls.
"""

from __future__ import annotations

import pytest
import allure

from datetime import UTC, datetime


pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 S3 Data Store"),
]


@pytest.fixture
def s3_bucket():
    """Create mock S3 bucket with test data using moto."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="research-data")

        # Seed test files
        s3.put_object(
            Bucket="research-data",
            Key="raw/firebase_export.json",
            Body=b'{"events": []}',
        )
        s3.put_object(
            Bucket="research-data",
            Key="raw/transcripts/interview_001.txt",
            Body=b"Interview transcript content",
        )
        s3.put_object(
            Bucket="research-data",
            Key="processed/participant_profiles.csv",
            Body=b"name,sessions\nuser_01,12",
        )

        yield s3


@allure.story("QC-047.03 S3 Scanner")
class TestS3Scanner:
    """Unit tests for S3Scanner using moto mock."""

    @allure.title("Scanner lists all files in bucket")
    def test_list_all_files(self, s3_bucket):
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=s3_bucket)
        files = scanner.list_files(bucket="research-data")

        assert len(files) == 3
        keys = {f.key for f in files}
        assert "raw/firebase_export.json" in keys
        assert "raw/transcripts/interview_001.txt" in keys
        assert "processed/participant_profiles.csv" in keys

    @allure.title("Scanner filters by prefix")
    def test_list_files_with_prefix(self, s3_bucket):
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=s3_bucket)
        files = scanner.list_files(bucket="research-data", prefix="raw/")

        assert len(files) == 2
        keys = {f.key for f in files}
        assert "raw/firebase_export.json" in keys
        assert "raw/transcripts/interview_001.txt" in keys

    @allure.title("Scanner returns RemoteFile with correct metadata")
    def test_remote_file_metadata(self, s3_bucket):
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=s3_bucket)
        files = scanner.list_files(bucket="research-data", prefix="raw/firebase")

        assert len(files) == 1
        rf = files[0]
        assert rf.key == "raw/firebase_export.json"
        assert rf.size_bytes > 0
        assert rf.last_modified is not None
        assert rf.filename == "firebase_export.json"
        assert rf.extension == ".json"

    @allure.title("Scanner returns empty list for nonexistent prefix")
    def test_list_files_empty_prefix(self, s3_bucket):
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=s3_bucket)
        files = scanner.list_files(bucket="research-data", prefix="nonexistent/")

        assert files == []

    @allure.title("Scanner downloads file content")
    def test_download_file(self, s3_bucket, tmp_path):
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=s3_bucket)
        local_path = tmp_path / "firebase_export.json"

        scanner.download_file(
            bucket="research-data",
            key="raw/firebase_export.json",
            local_path=str(local_path),
        )

        assert local_path.exists()
        content = local_path.read_text()
        assert '{"events": []}' in content

    @allure.title("Scanner uploads file to S3")
    def test_upload_file(self, s3_bucket, tmp_path):
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=s3_bucket)

        # Create a local file to upload
        local_file = tmp_path / "codebook.txt"
        local_file.write_text("Theme: Engagement\nTheme: Frustration")

        scanner.upload_file(
            bucket="research-data",
            key="coded/codebook.txt",
            local_path=str(local_file),
        )

        # Verify it's in S3
        result = s3_bucket.get_object(Bucket="research-data", Key="coded/codebook.txt")
        body = result["Body"].read().decode()
        assert "Engagement" in body
