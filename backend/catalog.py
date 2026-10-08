"""Public catalog contract. No unverified research is executable."""
from copy import deepcopy

DEMO = {
    "id": "demo-sbd-001", "version": 1, "title": "SBD 기록 연습",
    "status": "DEMO_ONLY", "source_type": "DEMO", "runnable": False,
    "description": "앱 동작 확인용 예시이며 논문 검증 루틴이 아닙니다.",
    "sessions": [{"id": "demo-session", "title": "연습 세션",
                  "exercises": [{"id": "squat", "name": "Squat", "sets": 3, "reps": 5, "rest_seconds": 180}]}]
}

def public_catalog(records):
    """Publish only explicitly released, source-backed, immutable versions."""
    result = []
    for record in records:
        if (record.get("status") == "PUBLISHED_PROTOCOL"
                and record.get("runnable") is True
                and record.get("source_type") == "RESEARCH"
                and record.get("source_sha256")
                and record.get("release_id")
                and isinstance(record.get("version"), int)
                and record["version"] > 0
                and record.get("sessions")):
            result.append(deepcopy(record))
    return result

def preview_catalog():
    """Visible demo for integration tests; intentionally not executable research."""
    return [deepcopy(DEMO)]
