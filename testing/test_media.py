"""Image upload validation, privacy cleaning, vision results, failure handling."""
import io

from PIL import Image

from app.services import llm_provider


def jpeg(color=(200, 80, 20), size=(640, 480), gps=False):
    im = Image.new("RGB", size, color)
    for x in range(0, size[0], 16):  # some edges so it is not 'blurry'
        for y in range(size[1]):
            im.putpixel((x, y), (255, 255, 255))
    buf = io.BytesIO()
    if gps:
        exif = Image.Exif()
        exif[0x8825] = {1: "N", 2: (12.0, 58.0, 0.0)}
        im.save(buf, "JPEG", exif=exif)
    else:
        im.save(buf, "JPEG")
    return buf.getvalue()


def upload(client, d, files):
    return client.post(f"/api/v1/incidents/{d['incident_id']}/media", headers={"X-Tracking-Token": d["tracking_token"]},
                       files=[("files", (n, b, "image/jpeg")) for n, b in files])


def fake_vision(data):
    return lambda system, user, image, timeout=None: llm_provider.LLMResult(
        ok=True, provider="test", model="fake-vl", latency_ms=12, text="{}", data=data)


def test_invalid_and_oversized_files_rejected(client, report):                        # 28
    d = report("Fire in the market")
    res = upload(client, d, [("a.jpg", b"not an image"), ("b.jpg", b"\xff\xd8" + b"0" * (9 * 1024 * 1024))]).json()["results"]
    assert [r["accepted"] for r in res] == [False, False]
    assert "larger than" in res[1]["error"]


def test_exif_stripped_and_duplicate_detected(client, report, auth):                  # 24
    d = report("Fire in the market")
    img = jpeg(gps=True)
    r1 = upload(client, d, [("a.jpg", img)]).json()["results"][0]
    r2 = upload(client, d, [("a.jpg", img)]).json()["results"][0]
    assert r1["accepted"] and r2["duplicate"] is True and r1["media_id"] == r2["media_id"]
    f = client.get(f"/api/v1/incidents/{d['incident_id']}/media/{r1['media_id']}/file",
                   headers={"X-Tracking-Token": d["tracking_token"]})
    assert f.status_code == 200
    assert not Image.open(io.BytesIO(f.content)).getexif()                            # GPS removed
    m = client.get(f"/api/v1/incidents/{d['incident_id']}/media", headers=auth["ADMIN"]).json()
    assert m[0]["exif_gps_present"] is True


def test_vision_disabled_keeps_incident(client, report):                               # vision unavailable
    d = report("Smoke from the warehouse")
    upload(client, d, [("a.jpg", jpeg())])
    t = client.get(f"/api/v1/incidents/{d['incident_id']}/track", headers={"X-Tracking-Token": d["tracking_token"]}).json()
    assert t["media"][0]["status"] == "NOT_ANALYZED" and t["status"] == "REPORTED"


def test_fire_image_corroborates_and_routes(client, report, auth, monkeypatch, unique_point):   # 3, 21
    monkeypatch.setattr("app.core.config.settings.VISION_PROVIDER", "test")
    monkeypatch.setattr(llm_provider, "analyze_image_json", fake_vision({
        "scene_category": "fire", "image_quality": "good", "visible_person_count": 2,
        "visible_evidence": [{"finding": "visible_flames", "description": "Flames from a window", "confidence": "high"},
                             {"finding": "person_on_ground", "description": "A man lying injured and bleeding", "confidence": "medium"}],
        "potential_hazards": ["fire spread"], "uncertainties": []}))
    lat, lng = unique_point()
    d = report("Something is wrong at the building, please come", lat, lng)
    upload(client, d, [("f.jpg", jpeg((240, 120, 0)))])
    v = client.get(f"/api/v1/control-room/incidents/{d['incident_id']}", headers=auth["ADMIN"]).json()
    img = v["image_evidence"][0]
    assert img["status"] in ("ANALYSIS_COMPLETED", "REVIEW_REQUIRED")
    assert img["injury_assessment"] == "cannot_be_determined_from_image"
    lying = next(f for f in img["findings"] if f["finding"] == "person_on_ground")
    assert lying["description"] == ""                       # medical / identity wording removed
    assert "visible_flames" in [f["finding"] for f in img["findings"]]
    assert next(r for r in v["routing"] if r["department"] == "FIRE")["included"]


def test_vision_failure_marks_failed_not_blocking(client, report, monkeypatch):        # 27
    monkeypatch.setattr("app.core.config.settings.VISION_PROVIDER", "test")
    monkeypatch.setattr(llm_provider, "analyze_image_json",
                        lambda *a, **k: llm_provider.LLMResult(ok=False, provider="test", error="timeout after 60s"))
    d = report("Flooded underpass")
    upload(client, d, [("a.jpg", jpeg((20, 60, 200)))])
    t = client.get(f"/api/v1/incidents/{d['incident_id']}/track", headers={"X-Tracking-Token": d["tracking_token"]}).json()
    assert t["media"][0]["status"] == "PROCESSING_FAILED" and t["category"] == "flood"


def test_irrelevant_or_contradictory_image_needs_review(client, report, auth, monkeypatch):   # 23, 29
    monkeypatch.setattr("app.core.config.settings.VISION_PROVIDER", "test")
    monkeypatch.setattr(llm_provider, "analyze_image_json", fake_vision({
        "scene_category": "unrelated", "image_quality": "good",
        "visible_evidence": [{"finding": "no_emergency_visible", "description": "A plate of food", "confidence": "high"}]}))
    d = report("Road accident near the toll gate, one injured")
    upload(client, d, [("a.jpg", jpeg((10, 200, 10)))])
    img = client.get(f"/api/v1/incidents/{d['incident_id']}/media", headers=auth["ADMIN"]).json()[0]
    assert img["status"] == "REVIEW_REQUIRED" and img["recommended_review"] is True


def test_media_requires_token_or_routed_user(client, report, auth):
    d = report("Fire in the market")
    r = upload(client, d, [("a.jpg", jpeg((1, 2, 3)))]).json()["results"][0]
    url = f"/api/v1/incidents/{d['incident_id']}/media/{r['media_id']}/file"
    assert client.get(url).status_code == 403
    assert client.get(url, headers=auth["DISASTER"]).status_code == 403
