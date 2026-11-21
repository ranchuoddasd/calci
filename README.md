# IP Subnet Allocation Analyzer

A lightweight web tool for analyzing IPv4 address allocation within a parent CIDR block. Upload JSON files describing a parent network and allocated subnets to calculate total, allocated, and free address space and identify free CIDR ranges.

## Features

- IPv4 CIDR validation and normalization
- Parent-network address capacity
- Allocated address count
- Remaining address count and utilization
- Consolidation of overlapping or adjacent allocations
- Free address ranges summarized as CIDR blocks
- File-upload interface and JSON API

## Requirements

- Python 3.9+
- Flask

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install Flask
python app.py
```

Open http://127.0.0.1:5001 in your browser.

## Input file examples

Parent network file (`big-block.json`):

```json
{ "big_block": "10.16.0.0/16" }
```

Allocated subnet file (`allocated-subnets.json`):

```json
{
  "allocated_subnets": [
    "10.16.0.0/24",
    "10.16.1.0/24",
    "10.16.3.0/24",
    "10.16.10.0/23"
  ]
}
```

## API

### Upload-based analysis

`POST /api/analyze` — multipart form upload with fields `big_block_file` and `allocated_subnets_file`.

### JSON analysis

`POST /api/analyze-json` — JSON body:

```json
{
  "big_block": "10.16.0.0/16",
  "allocated_subnets": ["10.16.0.0/24", "10.16.1.0/24"]
}
```

## Limitations and safety

- IPv4 only.
- This is a local prototype. Validate results independently before using them for production IPAM changes.
- Do not upload sensitive production addressing data to a publicly hosted instance.
- The development server is intended for local use; do not expose it directly to the internet.

## Roadmap

- Add automated tests for overlap, containment, invalid CIDRs, and edge cases.
- Add export options and visual address-space breakdown.
- Add Docker packaging and CI validation.
- Improve API error handling and upload limits.
