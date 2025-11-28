from pathlib import Path
from typing import Tuple
from ..config import settings


def get_vector_paths(
    user_id: int,
    subject_id: int,
    conversation_id: int
) -> Tuple[str, str]:
    """
    Tạo đường dẫn cho vector store của conversation
    
    Returns:
        Tuple[str, str]: (index_path, meta_path)
    """
    # Tạo thư mục base
    base_path = Path(settings.INDEX_DIR) / f"user_{user_id}" / f"subject_{subject_id}"
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Đường dẫn index và metadata
    index_path = base_path / f"conv_{conversation_id}.index"
    meta_path = base_path / f"conv_{conversation_id}.json"
    
    return str(index_path), str(meta_path)


def delete_vector_files(index_path: str, meta_path: str) -> None:
    """
    Xóa các file vector store
    """
    import os
    
    try:
        if os.path.exists(index_path):
            os.remove(index_path)
        
        if os.path.exists(meta_path):
            os.remove(meta_path)
            
    except Exception as e:
        print(f"Failed to delete vector files: {e}")
