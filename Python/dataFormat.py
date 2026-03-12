import json
import uuid
from datetime import datetime
from typing import Any, Dict

class JsonChunk:
    def __init__(self, chunk_number: int, total_chunks: int, data: str, 
                 id: uuid.UUID = None, group_id = None, timestamp: datetime = None):
        self.id = id
        self.group_id = group_id
        self.chunk_number = chunk_number
        self.total_chunks = total_chunks
        self.data = data
        self.timestamp = timestamp
    
    def to_dict(self):
        """Ensure Python dictionary keys match .NET PascalCase property names."""
        return {
            "ID": str(self.id),
            "GroupID": str(self.group_id),
            "ChunkNumber": self.chunk_number,
            "TotalChunks": self.total_chunks,
            "Data": self.data,
            "Timestamp": self.timestamp.isoformat()
        }