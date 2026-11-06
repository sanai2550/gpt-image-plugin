# gpt-image — Claude Code plugin cho OpenAI GPT Image 2.6

Tạo và chỉnh sửa ảnh bằng `gpt-image-2.6-flare` (nhanh) và `gpt-image-2.6-sunburst` (chi tiết, edit chính xác).
Hỗ trợ: PNG/JPEG/WebP, nền trong suốt, logo SVG, GIF lặp, edit nhiều ảnh tham chiếu, edit theo `markup`.

## Cài đặt

```bash
export OPENAI_API_KEY=sk-...
```

**Cách 1 – plugin (khuyên dùng):** đẩy thư mục này lên GitHub, rồi trong Claude Code:
```
/plugin marketplace add <github-user>/gpt-image-plugin
/plugin install gpt-image@gpt-image-marketplace
```
Hoặc thử trên máy: `claude --plugin-dir ./gpt-image-plugin`

**Cách 2 – chỉ skill:** copy `skills/gpt-image` vào `~/.claude/skills/gpt-image` (hoặc `.claude/skills/` của project).

## Dùng với provider khác (CLIProxyAPI, LiteLLM, ...)

Bất kỳ endpoint nào tương thích OpenAI và có `/v1/images/generations`, `/v1/images/edits`:

```bash
export GPT_IMAGE_BASE_URL=https://cliproxyapi.nanonai.net/v1
export GPT_IMAGE_API_KEY=<key trong api-keys của CLIProxyAPI>
python3 skills/gpt-image/scripts/gpt_image.py models    # xem model ảnh provider hỗ trợ
```

`GPT_IMAGE_*` được ưu tiên hơn `OPENAI_*`, nên bạn có thể dùng proxy cho ảnh mà không ảnh hưởng tool OpenAI khác.
Để Claude Code luôn có biến này, thêm vào `~/.claude/settings.json`:
```json
{ "env": { "GPT_IMAGE_BASE_URL": "https://cliproxyapi.nanonai.net/v1", "GPT_IMAGE_API_KEY": "..." } }
```

## Dùng

Cứ nói với Claude: *"Tạo cho tôi poster quảng cáo cà phê, chữ 'Cà Phê Sáng', dọc 1024x1536"* — skill sẽ tự viết prompt theo hướng dẫn của OpenAI, gọi API, mở ảnh kiểm tra và lặp lại nếu cần.

Gọi trực tiếp script:
```bash
python3 skills/gpt-image/scripts/gpt_image.py generate "PROMPT" -m sunburst -s 1536x1024 -q high
python3 skills/gpt-image/scripts/gpt_image.py edit "Change only ..." -i input.png
python3 skills/gpt-image/scripts/gpt_image.py --help
```

Biến môi trường: `GPT_IMAGE_API_KEY`/`OPENAI_API_KEY` (bắt buộc), `GPT_IMAGE_BASE_URL`/`OPENAI_BASE_URL`, `GPT_IMAGE_MODEL` (mặc định `flare`), `OPENAI_ORG_ID`.
