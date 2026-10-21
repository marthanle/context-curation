"""Index universal context and answer using semantic retrieval."""
import argparse
import hashlib
from pathlib import Path
from universal_context import load_corpus_documents as load_documents, split_text
from model_providers import add_model_arguments, validate_model_arguments, build_prompt, run_answers

COLLECTION = "universal_art_collection"
EMBED_MODEL = "all-minilm"


def get_collection(db_path="./local_vectordb"):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(db_path), settings=Settings(anonymized_telemetry=False)).get_or_create_collection(
        name=COLLECTION, embedding_function=None,
    )


def index_folder(collection, folder, chunk_size=600, overlap=80, documents=None, id_prefix=""):
    import ollama
    corpus = str(Path(folder).resolve())
    documents = load_documents(folder) if documents is None else documents
    current_ids = set()
    for document in documents:
        for index, chunk in enumerate(split_text(document.text, chunk_size, overlap)):
            identity = f"{id_prefix}{corpus}\0{document.source}\0{document.page}\0{index}"
            chunk_id = hashlib.sha256(identity.encode()).hexdigest()
            embeddings = ollama.embed(model=EMBED_MODEL, input=chunk, truncate=False)["embeddings"]
            collection.upsert(
                ids=[chunk_id], documents=[chunk], embeddings=embeddings,
                metadatas=[{"corpus": corpus, "source": document.source,
                            "kind": document.kind, "page": document.page,
                            "chunk": index, "embedding_model": EMBED_MODEL}],
            )
            current_ids.add(chunk_id)
    # Remove obsolete chunks only after successful extraction and embedding.
    old_ids = collection.get(where={"corpus": corpus}, include=[])["ids"]
    stale = sorted(set(old_ids) - current_ids)
    for start in range(0, len(stale), 100):
        collection.delete(ids=stale[start:start + 100])
    return len(current_ids)


def retrieve_context(collection, query, folder="prepared_context", top_k=3):
    import ollama
    if top_k < 1:
        raise ValueError("top_k must be positive")
    corpus = str(Path(folder).resolve())
    count = len(collection.get(where={"corpus": corpus}, include=[])["ids"])
    if not count:
        return ""
    embeddings = ollama.embed(model=EMBED_MODEL, input=query, truncate=False)["embeddings"]
    results = collection.query(query_embeddings=embeddings, n_results=min(top_k, count),
                               where={"corpus": corpus}, include=["documents", "metadatas"])
    sections = []
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        page = f", page {meta['page']}" if meta["page"] else ""
        sections.append(f"--- {meta['source']}{page} ({meta['kind']}, chunk {meta['chunk']}) ---\n{text}")
    return "\n\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", default="prepared_context")
    parser.add_argument("--db", default="./local_vectordb")
    parser.add_argument("--query", default="What are the key themes and how are they related? Cite the sources.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--chunk-size", type=int, default=600)
    parser.add_argument("--overlap", type=int, default=80)
    parser.add_argument("--skip-index", action="store_true", help="Query the existing index without reprocessing files")
    parser.add_argument("--index-only", action="store_true", help="Prepare Level 5 without making an answer-generation call")
    parser.add_argument("--updates", type=Path, help="Read a published Step 6 generation; requires --skip-index")
    add_model_arguments(parser, default_provider="gemini")
    args = parser.parse_args()
    validate_model_arguments(parser, args)
    if args.updates:
        if not args.skip_index or args.index_only:
            parser.error("--updates requires --skip-index; only Step 6 writes published generations")
        from update_store import resolve_cli_snapshot
        resolve_cli_snapshot(args, parser)
    if args.skip_index and args.index_only:
        parser.error("--index-only cannot be combined with --skip-index")
    if not 0 <= args.overlap < args.chunk_size or args.top_k < 1:
        parser.error("Require 0 <= overlap < chunk-size and top-k >= 1")
    collection = get_collection(args.db)
    if not args.skip_index:
        count = index_folder(collection, args.folder, args.chunk_size, args.overlap)
        print(f"Indexed {count} chunks.")
        if args.index_only:
            return 0
    context = retrieve_context(collection, args.query, args.folder, args.top_k)
    if not context:
        print("No indexed context found. Run without --skip-index for this folder first.")
        return 1
    print(context)
    return run_answers(build_prompt(context, args.query), args)


if __name__ == "__main__":
    raise SystemExit(main())
