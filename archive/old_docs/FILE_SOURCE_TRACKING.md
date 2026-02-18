# Summary: Added File Source Tracking

## Changes Made

### ✅ 1. Hybrid ETL Pipeline (`src/hybrid_etl_pipeline.py`)
Added file source tracking in document loading:
```python
documents.append({
    "id": str(uuid.uuid4()),
    "filename": file_path.name,
    "filepath": str(file_path.absolute()),        # NEW
    "relative_path": str(file_path.relative_to(self.data_dir)),  # NEW
    "text": text,
    "document_type": folder_name,
})
```

Added to document records and Qdrant payload:
- `filepath`: Full absolute path
- `relative_path`: Path relative to data directory
- `filename`: Original filename

### ✅ 2. ETL Pipeline (`src/etl_pipeline.py`)
Same changes applied to original ETL pipeline for consistency.

Added file info to both:
- Document-level points (in `land_documents` collection)
- Chunk-level points (in `land_chunks` collection)

### ✅ 3. Query Engine (`src/query_engine.py`)
Updated `SearchResult` dataclass:
```python
@dataclass
class SearchResult:
    # ... existing fields ...
    file_name: Optional[str] = None
    filepath: Optional[str] = None
    relative_path: Optional[str] = None
```

Updated `print_results()` to display:
```
📁 File: 1.จดทะเบียนประเภทโอนอสังหาริมทรัพย์.txt
📂 Path: คู่มือปชช.รายละเอียดเนื้อหา/1.จดทะเบียน...
```

### ✅ 4. Hybrid Query Engine (`src/hybrid_query_engine.py`)
Same updates applied to `HybridSearchResult` and `print_results()`.

## Benefits

1. **Traceability**: Can trace back to original source file
2. **Debugging**: Easier to identify which files have issues
3. **Citation**: Can cite source document in answers
4. **Audit**: Track where information comes from
5. **Updates**: Easy to identify which files need re-indexing

## Example Output

```
📄 Result 1
Score: 0.8542
Document: จดทะเบียนประเภทโอนอสังหาริมทรัพย์...
Type: คู่มือปชช | Level: 2
Chunk Type: documents_table_part
📁 File: 1.จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ (N).txt
📂 Path: คู่มือปชช.รายละเอียดเนื้อหา/1.จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ (N).txt
Section: รายการเอกสารหลักฐานประกอบการยื่นคำขอ
```

## Database Schema

File information stored in:
- `document_info.file_name`
- `document_info.filepath`
- `document_info.relative_path`

Can filter/search by these fields in future queries.
