from __future__ import annotations

import io
import zipfile
from typing import Any

from app.services.pdf import create_certificate_pdf, create_heatmap_pdf, create_summary_pdf


def build_dossier(
    form16_bytes: bytes,
    summary_data: dict[str, Any],
    full_name: str,
    tx_hash: str,
) -> bytes:
    summary_pdf = create_summary_pdf(summary_data)
    heatmap_pdf = create_heatmap_pdf()
    certificate_pdf = create_certificate_pdf(full_name, tx_hash)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("form16.pdf", form16_bytes)
        zipf.writestr("summary.pdf", summary_pdf)
        zipf.writestr("heatmap.pdf", heatmap_pdf)
        zipf.writestr("certificate.pdf", certificate_pdf)
    return buffer.getvalue()
