"""Extract reported table cells, not executable prescriptions, from PMC6162635 JATS."""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/research/coaching/sources/PMC6162635.xml"
OUTPUT = ROOT / "data/research/coaching/pilot2018-reported-tables.json"

def extract(raw):
    root = ET.fromstring(raw)
    doi = root.findtext(".//article-id[@pub-id-type='doi']")
    if doi != "10.3390/sports6030086":
        raise ValueError("Unexpected source")
    tables = []
    for table in root.findall(".//table-wrap"):
        rows = []
        for row in table.findall(".//tr"):
            rows.append([{
                "text": " ".join("".join(cell.itertext()).split()),
                "rowspan": int(cell.get("rowspan", "1")),
                "colspan": int(cell.get("colspan", "1"))
            } for cell in row])
        caption = table.find("caption")
        tables.append({
            "source_locator": table.get("id"),
            "caption": " ".join("".join(caption.itertext()).split()),
            "rows": rows
        })
    if len(tables) != 6:
        raise ValueError("Expected six reported tables")
    return {
        "schema_version": 1,
        "doi": doi,
        "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6162635/",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "attribution": "Androulakis-Korakakis et al. (2018), Sports 6(3):86",
        "license": "CC-BY-4.0",
        "data_role": "reported_table_cells_not_prescriptions",
        "scientific_approval": False,
        "release_status": "not_released",
        "tables": tables,
        "limitations": [
            "Weekly ranges must not be expanded into invented daily prescriptions.",
            "Week 10 MAX deadlift frequency conflicts between narrative and Table 2.",
            "MAX participant 4 total change has conflicting signs in results prose and Table 5.",
            "PER participant 1 post total precision differs from sum of component lifts.",
            "Individual outcomes are not personal growth forecasts.",
            "Supplement download returned a verification page, not a ZIP."
        ]
    }

if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(extract(SOURCE.read_bytes()), ensure_ascii=False, indent=2) + "\n")
