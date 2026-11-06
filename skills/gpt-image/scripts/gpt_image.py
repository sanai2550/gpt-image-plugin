#!/usr/bin/env python3
"""Generate or edit images with OpenAI GPT Image 2.6 (Flare / Sunburst).

Standard library only (no `pip install` needed). Talks directly to
POST /v1/images/generations and POST /v1/images/edits so newer fields
(complexity, markup, svg/gif output, frame_count...) work even if the
installed OpenAI SDK does not know them yet.

Provider: works with any OpenAI-compatible endpoint (OpenAI, CLIProxyAPI, LiteLLM, ...).
  GPT_IMAGE_BASE_URL (or OPENAI_BASE_URL)  e.g. https://cliproxyapi.example.com/v1
  GPT_IMAGE_API_KEY  (or OPENAI_API_KEY)
  GPT_IMAGE_MODEL    default model alias/id (flare)

Examples
  gpt_image.py models
  gpt_image.py generate "A paper-cut stadium celebration" -o out/champions.png
  gpt_image.py generate "Field & Flour bakery logo" --format svg --background transparent
  gpt_image.py generate "Monkey lifts a lantern, loops" --format gif --size 512x512 \
      --frame-count 9 --frame-duration-ms 200
  gpt_image.py edit "Recolor the vase inside the red circle to cobalt blue..." \
      -i kitchen.webp --markup circle.png
  gpt_image.py edit "Place the dog from image 2 next to the woman in image 1" \
      -i scene.jpg -i dog.jpg
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

MODELS = {
    "flare": "gpt-image-2.6-flare",       # faster, smaller
    "sunburst": "gpt-image-2.6-sunburst",  # more detail, precise edits
}
QUALITIES = ["auto", "low", "medium", "high", "xhigh", "max"]
COMPLEXITIES = ["low", "medium", "high"]
BACKGROUNDS = ["auto", "opaque", "transparent"]
FORMATS = ["png", "jpeg", "webp", "svg", "gif"]


def die(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def check_size(size: str) -> None:
    if size == "auto":
        return
    try:
        w, h = (int(x) for x in size.lower().split("x"))
    except ValueError:
        die(f"size must be 'auto' or WIDTHxHEIGHT, got {size!r}")
    if w % 16 or h % 16:
        die(f"size {size}: both edges must be multiples of 16")
    if max(w, h) / min(w, h) > 3:
        die(f"size {size}: aspect ratio must be between 1:3 and 3:1")


def build_fields(a: argparse.Namespace) -> dict:
    model = MODELS.get(a.model, a.model)
    f: dict = {"model": model, "prompt": a.prompt}
    for key, val in [
        ("size", a.size), ("quality", a.quality), ("complexity", a.complexity),
        ("background", a.background), ("output_format", a.format), ("n", a.n),
        ("output_compression", a.compression), ("frame_count", a.frame_count),
        ("frame_duration_ms", a.frame_duration_ms),
    ]:
        if val is not None:
            f[key] = val
    for kv in a.extra or []:
        k, _, v = kv.partition("=")
        try:
            f[k] = json.loads(v)
        except json.JSONDecodeError:
            f[k] = v
    return f


def validate(a: argparse.Namespace, f: dict) -> None:
    if a.size:
        check_size(a.size)
    fmt = f.get("output_format")
    if a.compression is not None and fmt not in ("jpeg", "webp"):
        die("--compression only works with --format jpeg or webp")
    if fmt in ("svg", "gif") and a.cmd == "edit":
        die(f"{fmt} output is only supported for generations")
    if a.background == "transparent" and fmt == "jpeg":
        die("transparent background needs png, webp or svg")
    if (a.frame_count or a.frame_duration_ms) and fmt != "gif":
        die("--frame-count/--frame-duration-ms require --format gif")
    if a.cmd == "edit":
        if not a.image:
            die("edit needs at least one --image")
        for p in a.image + ([a.markup] if a.markup else []) + ([a.mask] if a.mask else []):
            if not Path(p).is_file():
                die(f"file not found: {p}")
        if a.markup and a.mask:
            die("omit --mask when sending --markup")


def multipart(fields: dict, files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n".encode()
        out += (json.dumps(v) if isinstance(v, (dict, list)) else str(v)).encode() + b"\r\n"
    for name, path in files:
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; "
                f"filename=\"{path.name}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
        out += path.read_bytes() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def api_base() -> str:
    return (os.environ.get("GPT_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
            or "https://api.openai.com/v1").rstrip("/")


def api_key() -> str | None:
    return os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")


def call(url: str, body: bytes | None, ctype: str, key: str, timeout: int) -> dict:
    req = urllib.request.Request(url, data=body, method="POST" if body is not None else "GET",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": ctype,
                                          "User-Agent": "gpt-image-skill/0.2"})
    org = os.environ.get("OPENAI_ORG_ID")
    if org:
        req.add_header("OpenAI-Organization", org)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        try:
            detail = json.loads(detail)["error"]["message"]
        except Exception:
            pass
        die(f"API {e.code}: {detail}", 1)


def output_paths(out: str | None, fmt: str, n: int) -> list[Path]:
    ext = "jpg" if fmt == "jpeg" else fmt
    if out:
        base = Path(out)
        if base.suffix == "":
            base = base / f"image-{time.strftime('%Y%m%d-%H%M%S')}.{ext}"
    else:
        base = Path("generated-images") / f"image-{time.strftime('%Y%m%d-%H%M%S')}.{ext}"
    if n == 1:
        return [base]
    return [base.with_name(f"{base.stem}-{i}{base.suffix}") for i in range(1, n + 1)]


def main() -> None:
    p = argparse.ArgumentParser(description="OpenAI GPT Image 2.6 generate/edit")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("models", help="list models the provider exposes (filter: image)")
    m.add_argument("--all", action="store_true", help="show every model, not only image ones")
    for name in ("generate", "edit"):
        s = sub.add_parser(name)
        s.add_argument("prompt", help="prompt text, or @file.txt to read it from a file")
        s.add_argument("-m", "--model", default=os.environ.get("GPT_IMAGE_MODEL", "flare"),
                       help="flare | sunburst | full model id (default: flare)")
        s.add_argument("-s", "--size", help="auto, 1024x1024, 1536x1024, 1024x1536, or WxH")
        s.add_argument("-q", "--quality", choices=QUALITIES)
        s.add_argument("-c", "--complexity", choices=COMPLEXITIES,
                       help="planning depth; API default is high")
        s.add_argument("-b", "--background", choices=BACKGROUNDS)
        s.add_argument("-f", "--format", choices=FORMATS, default="png")
        s.add_argument("-n", type=int, default=1, help="number of images")
        s.add_argument("--compression", type=int, help="0-100, jpeg/webp only")
        s.add_argument("--frame-count", type=int, help="gif only")
        s.add_argument("--frame-duration-ms", type=int, help="gif only")
        s.add_argument("-o", "--out", help="output file or directory")
        s.add_argument("--extra", action="append", metavar="KEY=VALUE",
                       help="extra raw API field (repeatable)")
        s.add_argument("--timeout", type=int, default=600)
        s.add_argument("--dry-run", action="store_true", help="print request, don't call API")
        if name == "edit":
            s.add_argument("-i", "--image", action="append", default=[],
                           help="input image (repeat; order = image 1, 2, ...)")
            s.add_argument("--markup", help="transparent PNG overlay, same size as image 1")
            s.add_argument("--mask", help="mask PNG for masked edits")
    a = p.parse_args()
    if a.cmd == "models":
        key = api_key() or die("GPT_IMAGE_API_KEY / OPENAI_API_KEY is not set")
        ids = sorted(x.get("id", "") for x in call(f"{api_base()}/models", None, "application/json",
                                                     key, 60).get("data", []))
        print("\n".join(i for i in ids if a.all or "image" in i or "dall" in i) or
              "(no image models listed; try --all)")
        return
    if a.prompt.startswith("@"):
        a.prompt = Path(a.prompt[1:]).read_text().strip()

    fields = build_fields(a)
    validate(a, fields)

    base = api_base()
    if a.cmd == "generate":
        url, body, ctype = f"{base}/images/generations", json.dumps(fields).encode(), "application/json"
        files: list = []
    else:
        files = [("image[]", Path(x)) for x in a.image]
        if a.markup:
            files.append(("markup", Path(a.markup)))
        if a.mask:
            files.append(("mask", Path(a.mask)))
        url = f"{base}/images/edits"
        body, ctype = multipart(fields, files)

    if a.dry_run:
        print(json.dumps({"url": url, "fields": fields,
                          "files": [f"{n}={p}" for n, p in files]}, indent=2))
        return

    key = api_key()
    if not key:
        die("GPT_IMAGE_API_KEY / OPENAI_API_KEY is not set")

    t0 = time.time()
    resp = call(url, body, ctype, key, a.timeout)
    data = resp.get("data") or []
    if not data:
        die(f"no images returned: {json.dumps(resp)[:500]}", 1)

    paths = output_paths(a.out, fields["output_format"], len(data))
    saved = []
    for item, path in zip(data, paths):
        path.parent.mkdir(parents=True, exist_ok=True)
        if item.get("b64_json"):
            path.write_bytes(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            u = item["url"]
            if u.startswith("data:"):
                path.write_bytes(base64.b64decode(u.split(",", 1)[1]))
            else:
                r = urllib.request.Request(u, headers={"User-Agent": "gpt-image-skill/0.2"})
                with urllib.request.urlopen(r, timeout=a.timeout) as resp_img:
                    path.write_bytes(resp_img.read())
        else:
            continue
        saved.append(str(path))
        if item.get("revised_prompt"):
            print(f"revised_prompt: {item['revised_prompt']}", file=sys.stderr)

    print(json.dumps({"model": fields["model"], "saved": saved,
                      "seconds": round(time.time() - t0, 1),
                      "usage": resp.get("usage")}, indent=2))


if __name__ == "__main__":
    main()
