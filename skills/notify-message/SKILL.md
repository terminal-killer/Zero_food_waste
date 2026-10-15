---
name: notify-message
description: "MANDATORY TRIGGER: You MUST activate this skill immediately when a pickup route is confirmed to produce ready-to-copy multilingual WhatsApp notification messages for the donor, recipient, and volunteer. Never compose notification texts manually."
---

# Multilingual WhatsApp Notification Generator

Formats concise, actionable WhatsApp alerts in English, Hindi, and Odia for all stakeholders: donor, recipient organization, and assigned delivery volunteer.

## Capabilities
- Formats ready-to-copy WhatsApp messages with emojis, bold tags, and clear instructions.
- Includes mission ID, pickup ETA, contact numbers, item breakdown, and strict safety consumption deadlines.
- Automatically handles single-stop and multi-stop split deliveries.
- Supports 3 languages: English, Hindi, and Odia.
- **Offline & Mock Compliant:** Outputs clean text blocks; does not call external messaging APIs.

## Usage
Run via Python script:

```bash
python skills/notify-message/scripts/generate_messages.py '<payload_json>'
```
