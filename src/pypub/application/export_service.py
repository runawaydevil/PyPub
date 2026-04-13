import json
import zipfile

class ExportService:
    def __init__(self, post_service):
        self.post_service = post_service
        
    def export_drafts(self, account_id: int, out_path: str) -> None:
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
