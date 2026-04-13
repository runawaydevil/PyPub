import json
import zipfile
from pathlib import Path
from typing import List
from pypub.domain.models import Draft

class ExportService:
    def __init__(self, post_service, db_path: Path):
        self.post_service = post_service
        self.db_path = db_path
        
    def export_drafts(self, account_id: int, out_path: str):
        """
        Zips all drafts for an account into a single .pypub archive.
        """
        drafts = self.post_service.db.get_drafts(account_id)
        
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            manifest = []
            for d in drafts:
                d_dict = d.model_dump(mode="json")
                manifest.append({"id": d.id, "title": d.title})
                
                # Write draft JSON
                zf.writestr(f"drafts/draft_{d.id}.json", json.dumps(d_dict, indent=2))
                
            # Write global manifest
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
