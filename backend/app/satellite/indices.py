def ndvi(nir: float, red: float) -> float | None:
    """Normalized Difference Vegetation Index, returning None for a zero denominator."""
    denominator = nir + red
    return None if denominator == 0 else (nir - red) / denominator


def clear_sentinel_qa60(qa60: int) -> bool:
    """Sentinel-2 QA60 bits 10 (opaque cloud) and 11 (cirrus) must both be unset."""
    return (qa60 & (1 << 10)) == 0 and (qa60 & (1 << 11)) == 0

