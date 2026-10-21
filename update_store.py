"""Resolve an atomically published pair of immutable vector/graph artifacts."""
import json
from pathlib import Path
import re
import threading

from graph_context import corpus_fingerprint


def read_current(updates, folder):
    root = Path(updates).resolve()
    try:
        data = json.loads((root / "current.json").read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("No published update. Run level6_auto_update.py --once first.") from exc
    if not isinstance(data, dict) or data.get("version") != 1 or data.get("corpus") != str(Path(folder).resolve()):
        raise ValueError("Update manifest version/corpus mismatch; use the watcher's --folder and --updates.")
    generation = data.get("generation", "")
    if not isinstance(generation, str) or not re.fullmatch(r"[0-9a-f]{32}", generation):
        raise ValueError("Invalid update generation")
    directory = root / "generations" / generation
    if not (directory / "db/chroma.sqlite3").is_file() or not (directory / "graph.json").is_file():
        raise ValueError("Published generation files are missing; rerun the updater with --force.")
    if not isinstance(data.get("corpus_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", data["corpus_sha256"]):
        raise ValueError("Published generation has no corpus fingerprint")
    return data, directory / "db", directory / "graph.json"


def snapshot_status(updates, folder, manifest):
    try:
        freshness = "current" if corpus_fingerprint(folder) == manifest["corpus_sha256"] else "stale"
    except (OSError, ValueError):
        freshness = "source unavailable"
    state = {}
    try:
        state = json.loads((Path(updates) / "status.json").read_text(encoding="utf-8"))
        if state.get("corpus") != str(Path(folder).resolve()):
            state = {}
    except (OSError, ValueError):
        pass
    return {"generation": manifest["generation"], "published_at": manifest["published_at"],
            "freshness": freshness, "updater": state,
            "note": "A tool call uses one complete generation. Check generation IDs before combining separate calls. "
                    "Updater status records its last activity, not proof that its process is still running."}


class LiveCorpusTools:
    """Resolve the current manifest once per tool call; never mutate a served generation."""
    def __init__(self, folder, updates):
        self.folder, self.updates = Path(folder).resolve(), Path(updates).resolve()
        self.generation, self.tools = None, None
        self.lock = threading.Lock()

    def call(self, method, *args):
        try:
            manifest, db, graph = read_current(self.updates, self.folder)
        except (ValueError, OSError) as exc:
            if method == "get_corpus_status":
                return {"ready": False, "graph": {"ready": False}, "message": str(exc)}
            raise
        # Calls get a local reference so a concurrent call switching generations
        # cannot change the collection/graph used by this call.
        from corpus_tools import CorpusTools
        with self.lock:
            if self.generation != manifest["generation"]:
                service = CorpusTools(self.folder, db, graph_path=graph,
                                      snapshot_fingerprint=manifest["corpus_sha256"])
                self.tools, self.generation = service, manifest["generation"]
            else:
                service = self.tools
        result = getattr(service, method)(*args)
        result["snapshot"] = snapshot_status(self.updates, self.folder, manifest)
        if method == "get_corpus_status":
            # Preserve collection/read errors; zero chunks alone is valid.
            result["ready"] = "indexed_sources" in result
            result["freshness"] = result["snapshot"]["freshness"]
        return result

    def get_corpus_status(self):
        return self.call("get_corpus_status")

    def list_sources(self, offset=0, limit=25):
        return self.call("list_sources", offset, limit)

    def search_context(self, query, top_k=3):
        return self.call("search_context", query, top_k)

    def fetch_source_excerpt(self, chunk_id, radius=1):
        try:
            return self.call("fetch_source_excerpt", chunk_id, radius)
        except ValueError as exc:
            raise ValueError(f"{exc}. If a newer generation was published, repeat search_context first.") from exc

    def get_relationships(self, entity="", query="", limit=12):
        return self.call("get_relationships", entity, query, limit)


def resolve_cli_snapshot(args, parser):
    if not args.updates:
        return None
    try:
        manifest, db, graph = read_current(args.updates, args.folder)
        status = snapshot_status(args.updates, args.folder, manifest)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    args.db, args.graph = str(db), str(graph)
    print(f"Published generation {manifest['generation']}; freshness: {status['freshness']}.")
    return manifest["corpus_sha256"]
