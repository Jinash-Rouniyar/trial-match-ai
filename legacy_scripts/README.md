# Legacy scripts

Offline experiments that read **AACT pipe-delimited** exports under the repo’s `aact_data/` directory. They are **not** used by the Flask app or `trialmatch/`.

| Script | Purpose |
|--------|---------|
| `matcher.py` | Random-trial matching demo against local AACT subset + Synthea JSON |
| `create_subset.py` | Two fixed NCT IDs — same style pipeline (subset + patients) |
| `create_demo_set.py` | Build small `*_demo.txt` files from subset tables |

Run from anywhere; paths resolve to the **repository root** automatically:

```bash
python legacy_scripts/matcher.py
```

Requires GPU-friendly deps (torch, transformers) beyond the main app’s `requirements.txt`.
