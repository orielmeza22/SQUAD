"""RAG Indexer using ChromaDB for semantic code search."""
from typing import List, Optional, Dict
import os

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class RAGIndexer:
    def __init__(self, workspace: str, collection_name: str = "squad_workspace"):
        self.workspace = workspace
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def is_available(self) -> bool:
        return CHROMA_AVAILABLE

    def _ensure_client(self):
        if self._client is None:
            # Persistent DB inside workspace
            db_path = os.path.join(self.workspace, ".chroma_db")
            os.makedirs(db_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=db_path)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def index_file(self, filepath: str, content: str, language: str = "python") -> None:
        """Index a single file, split into chunks."""
        if not CHROMA_AVAILABLE:
            return
        self._ensure_client()
        
        # Clean path separator consistency
        filepath = filepath.replace('\\', '/')
        chunks = self._chunk_content(content, filepath)

        # Delete existing chunks to prevent stale index entries
        try:
            self._collection.delete(where={"source": filepath})
        except Exception:
            pass

        if not chunks:
            return

        documents = []
        ids = []
        metadatas = []
        for i, (chunk_text, start_line) in enumerate(chunks):
            documents.append(chunk_text)
            ids.append(f"{filepath}::chunk_{i}")
            metadatas.append({
                "source": filepath,
                "language": language,
                "start_line": start_line
            })

        self._collection.upsert(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

    def index_workspace(self) -> Dict[str, int]:
        """Index all code files in workspace. Returns {filename: chunk_count}."""
        stats = {}
        if not CHROMA_AVAILABLE:
            return stats
        if not os.path.exists(self.workspace):
            return stats

        for root, dirs, files in os.walk(self.workspace):
            # Skip hidden directories like .git and .chroma_db
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.endswith(('.py', '.js', '.ts', '.tsx', '.html', '.css', '.sql', '.md')):
                    filepath = os.path.join(root, f)
                    rel = os.path.relpath(filepath, self.workspace).replace('\\', '/')
                    # Skip config or report files if they shouldn't be indexed,
                    # but index them generally if they are code-like
                    if rel.startswith(".chroma_db/"):
                        continue
                    lang = f.split('.')[-1]
                    try:
                        with open(filepath, 'r', encoding='utf-8') as fh:
                            content = fh.read()
                        self.index_file(rel, content, lang)
                        stats[rel] = len(self._chunk_content(content, rel))
                    except Exception:
                        pass

        # Also index global/project skills if they exist
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        skills_dir = os.path.join(backend_root, "skills")
        if os.path.exists(skills_dir):
            for root, dirs, files in os.walk(skills_dir):
                for f in files:
                    if f.endswith(('.py', '.js', '.ts')):
                        filepath = os.path.join(root, f)
                        rel_skill = "skills/" + os.path.relpath(filepath, skills_dir).replace('\\', '/')
                        try:
                            with open(filepath, 'r', encoding='utf-8') as fh:
                                content = fh.read()
                            self.index_file(rel_skill, content, f.split('.')[-1])
                            stats[rel_skill] = len(self._chunk_content(content, rel_skill))
                        except Exception:
                            pass
        return stats

    def query(self, question: str, n_results: int = 5) -> List[Dict]:
        """Semantic search. Returns [{document, source, start_line, distance}]."""
        if not CHROMA_AVAILABLE:
            return []
        self._ensure_client()
        try:
            results = self._collection.query(
                query_texts=[question],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            items = []
            if results and "documents" in results and results["documents"]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    items.append({
                        "document": doc,
                        "source": meta.get("source", "unknown"),
                        "start_line": meta.get("start_line", 0),
                        "distance": dist,
                    })
            return items
        except Exception:
            return []

    def _chunk_content(self, content: str, filepath: str, max_chars: int = 1500, overlap: int = 200) -> List[tuple]:
        """Split file into overlapping chunks by lines."""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_len = 0
        start_line = 1

        for i, line in enumerate(lines):
            current_chunk.append(line)
            current_len += len(line) + 1
            if current_len >= max_chars:
                chunk_text = '\n'.join(current_chunk)
                chunks.append((chunk_text, start_line))
                # Overlap: keep last few lines
                overlap_lines = []
                overlap_len = 0
                for line_rev in reversed(current_chunk):
                    if overlap_len + len(line_rev) > overlap:
                        break
                    overlap_lines.insert(0, line_rev)
                    overlap_len += len(line_rev)
                current_chunk = overlap_lines
                current_len = sum(len(l) + 1 for l in current_chunk)
                start_line = i + 1 - len(overlap_lines) + 1

        if current_chunk and not (len(current_chunk) == 1 and current_chunk[0] == ''):
            chunks.append(('\n'.join(current_chunk), start_line))
        return chunks

    def clear(self) -> None:
        if not CHROMA_AVAILABLE:
            return
        self._ensure_client()
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None
