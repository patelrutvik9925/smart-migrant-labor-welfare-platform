"""
Cloud Object Storage client — supports both IBM COS (production) and local file storage (development/free tier).
Switch to IBM COS by setting COS_API_KEY in .env.
Original evidence is NEVER overwritten regardless of storage backend.
"""
import structlog
import pathlib
import shutil
from typing import Optional

from backend.utils.config import settings

log = structlog.get_logger()

_cos_client = None
_use_local = None


def _is_local_mode() -> bool:
    """Use local storage if COS credentials are not configured."""
    global _use_local
    if _use_local is None:
        _use_local = not settings.COS_API_KEY or settings.COS_API_KEY in (
            "your_cos_api_key", "", "your_production_cos_api_key"
        )
        if _use_local:
            log.info("Using local file storage (development mode). Set COS_API_KEY for IBM COS.")
        else:
            log.info("Using IBM Cloud Object Storage")
    return _use_local


def get_cos_client():
    global _cos_client
    if _cos_client is None and not _is_local_mode():
        import ibm_boto3
        from ibm_botocore.client import Config
        _cos_client = ibm_boto3.client(
            "s3",
            ibm_api_key_id=settings.COS_API_KEY,
            ibm_service_instance_id=settings.COS_INSTANCE_CRN,
            config=Config(signature_version="oauth"),
            endpoint_url=settings.COS_ENDPOINT,
        )
    return _cos_client


def _local_path(bucket: str, key: str) -> pathlib.Path:
    """Map a COS bucket+key to a local path under ./data/storage/"""
    p = pathlib.Path("./data/storage") / bucket / key
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


async def upload_worker_document(
    worker_id: str,
    filename: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """Upload a worker document. Returns the COS object key (or local path)."""
    import uuid
    key = f"worker-docs/{worker_id}/{uuid.uuid4()}/{filename}"

    if _is_local_mode():
        p = _local_path(settings.COS_BUCKET_WORKER_DOCS, key)
        p.write_bytes(file_bytes)
        log.info("Worker document saved locally", worker_id=worker_id, path=str(p))
    else:
        cos = get_cos_client()
        cos.put_object(
            Bucket=settings.COS_BUCKET_WORKER_DOCS,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        log.info("Worker document uploaded to COS", worker_id=worker_id, key=key)
    return key


async def upload_complaint_evidence(
    complaint_number: str,
    filename: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """
    Upload original complaint evidence.
    Object key is IMMUTABLE — original evidence is never overwritten.
    """
    import uuid
    key = f"complaint-evidence/{complaint_number}/original/{uuid.uuid4()}/{filename}"

    if _is_local_mode():
        p = _local_path(settings.COS_BUCKET_COMPLAINT_EVIDENCE, key)
        p.write_bytes(file_bytes)
        log.info("Complaint evidence saved locally", complaint_number=complaint_number, path=str(p))
    else:
        cos = get_cos_client()
        cos.put_object(
            Bucket=settings.COS_BUCKET_COMPLAINT_EVIDENCE,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        log.info("Complaint evidence uploaded to COS", complaint_number=complaint_number, key=key)
    return key


async def upload_ai_analysis(
    complaint_number: str,
    evidence_id: str,
    analysis_bytes: bytes,
) -> str:
    """
    Store AI analysis SEPARATELY from original evidence.
    Never overwrites the original.
    """
    import json
    key = f"complaint-evidence/{complaint_number}/ai-analysis/{evidence_id}/analysis.json"

    if _is_local_mode():
        p = _local_path(settings.COS_BUCKET_COMPLAINT_EVIDENCE, key)
        p.write_bytes(analysis_bytes)
    else:
        cos = get_cos_client()
        cos.put_object(
            Bucket=settings.COS_BUCKET_COMPLAINT_EVIDENCE,
            Key=key,
            Body=analysis_bytes,
            ContentType="application/json",
        )
    return key


async def verify_storage_connectivity() -> dict:
    """Health check — verifies storage backend is accessible."""
    if _is_local_mode():
        p = pathlib.Path("./data/storage")
        p.mkdir(parents=True, exist_ok=True)
        return {"backend": "local", "status": "ok", "path": str(p.resolve())}
    else:
        try:
            cos = get_cos_client()
            cos.head_bucket(Bucket=settings.COS_BUCKET_WORKER_DOCS)
            return {"backend": "ibm_cos", "status": "ok", "endpoint": settings.COS_ENDPOINT}
        except Exception as e:
            return {"backend": "ibm_cos", "status": "error", "error": str(e)}
