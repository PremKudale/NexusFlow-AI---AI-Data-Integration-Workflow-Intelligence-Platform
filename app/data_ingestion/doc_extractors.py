import re
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
try:
    import pymupdf as fitz
except ImportError:
    import fitz

class SemanticDocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    source_type: str  # 'pdf', 'spreadsheet', 'email', 'confluence', 'rest_api', 'erp'
    source_name: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentExtractor:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_text(self, text: str) -> List[str]:
        words = text.split()
        if len(words) <= self.chunk_size:
            return [text.strip()]
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk.strip())
            i += (self.chunk_size - self.overlap)
        return chunks

    def extract_pdf(self, file_path: str, tenant_id: str = "tenant_enterprise_corp") -> List[SemanticDocumentChunk]:
        path = Path(file_path)
        chunks = []
        doc = fitz.open(file_path)
        full_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                full_text.append(f"--- Page {page_num + 1} ---\n{text}")

        combined = "\n\n".join(full_text)
        splits = self._split_text(combined)
        for idx, text_part in enumerate(splits):
            chunk_id = f"pdf_{path.stem}_chk_{idx+1}"
            chunks.append(SemanticDocumentChunk(
                chunk_id=chunk_id,
                doc_id=path.stem,
                source_type="pdf",
                source_name=path.name,
                title=path.stem.replace("_", " ").title(),
                content=text_part,
                metadata={
                    "tenant_id": tenant_id,
                    "pages": len(doc),
                    "chunk_index": idx,
                    "file_path": str(path)
                }
            ))
        doc.close()
        return chunks

    def extract_spreadsheet(self, file_path: str, tenant_id: str = "tenant_enterprise_corp") -> List[SemanticDocumentChunk]:
        path = Path(file_path)
        chunks = []
        rows = []
        if path.suffix.lower() == ".csv":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                for idx, row in enumerate(reader):
                    row_str = " | ".join([f"{k}: {v}" for k, v in row.items() if v])
                    rows.append(row_str)
        else:
            import pandas as pd
            df = pd.read_excel(file_path)
            for idx, row in df.iterrows():
                row_str = " | ".join([f"{k}: {v}" for k, v in row.to_dict().items() if pd.notna(v)])
                rows.append(row_str)

        # Group rows into manageable chunks
        batch_size = 8
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            content = f"Dataset: {path.name}\n" + "\n".join(batch)
            chunk_id = f"sheet_{path.stem}_chk_{i//batch_size + 1}"
            chunks.append(SemanticDocumentChunk(
                chunk_id=chunk_id,
                doc_id=path.stem,
                source_type="spreadsheet",
                source_name=path.name,
                title=f"Spreadsheet: {path.stem}",
                content=content,
                metadata={
                    "tenant_id": tenant_id,
                    "row_range": f"{i}-{i+len(batch)}",
                    "file_path": str(path)
                }
            ))
        return chunks

    def extract_email(self, content_str: str, email_id: str, tenant_id: str = "tenant_enterprise_corp") -> List[SemanticDocumentChunk]:
        # Parse email headers & body
        subject = "Internal Enterprise Communication"
        sender = "system@enterprise.internal"
        date = "2026-11-20"

        for line in content_str.split("\n")[:10]:
            if line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
            elif line.lower().startswith("from:"):
                sender = line.split(":", 1)[1].strip()
            elif line.lower().startswith("date:"):
                date = line.split(":", 1)[1].strip()

        chunk = SemanticDocumentChunk(
            chunk_id=f"email_{email_id}_chk_1",
            doc_id=email_id,
            source_type="email",
            source_name=f"Email: {subject}",
            title=subject,
            content=content_str.strip(),
            metadata={
                "tenant_id": tenant_id,
                "sender": sender,
                "date": date,
                "email_id": email_id
            }
        )
        return [chunk]

    def extract_confluence_page(self, title: str, space: str, markdown_content: str, page_id: str, tenant_id: str = "tenant_enterprise_corp") -> List[SemanticDocumentChunk]:
        splits = self._split_text(markdown_content)
        chunks = []
        for idx, text_part in enumerate(splits):
            chunk = SemanticDocumentChunk(
                chunk_id=f"confluence_{page_id}_chk_{idx+1}",
                doc_id=page_id,
                source_type="confluence",
                source_name=f"Confluence: [{space}] {title}",
                title=title,
                content=f"Confluence Space: {space} | Page: {title}\n\n{text_part}",
                metadata={
                    "tenant_id": tenant_id,
                    "space": space,
                    "page_id": page_id,
                    "chunk_index": idx
                }
            )
            chunks.append(chunk)
        return chunks

    def extract_rest_api_payload(self, endpoint_name: str, payload: dict, tenant_id: str = "tenant_enterprise_corp") -> List[SemanticDocumentChunk]:
        formatted = json.dumps(payload, indent=2)
        chunk = SemanticDocumentChunk(
            chunk_id=f"api_{endpoint_name}_chk_1",
            doc_id=endpoint_name,
            source_type="rest_api",
            source_name=f"REST API: /{endpoint_name}",
            title=f"REST API Ingestion: {endpoint_name}",
            content=f"REST API Endpoint: {endpoint_name}\nResponse Payload:\n{formatted}",
            metadata={
                "tenant_id": tenant_id,
                "endpoint": endpoint_name
            }
        )
        return [chunk]

doc_extractor = DocumentExtractor()

