"""Watch prepared documents and publish complete vector/graph generations for MCP."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from build_graph import build
from graph_context import atomic_json, corpus_fingerprint
from level2_vector_rag import get_collection, index_folder
from model_providers import DEFAULT_MODELS, _safe_error, positive_int, gemini_thinking_config
from universal_context import load_corpus_documents
from update_store import read_current


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def writer_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "writer.lock"
    try:
        handle = path.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise ValueError("An updater lock exists. Stop the other updater; after a crash, verify no updater "
                         "is running before removing writer.lock and restarting.") from exc
    try:
        with handle:
            json.dump({"pid": os.getpid(), "started_at": now()}, handle)
        yield
    finally:
        path.unlink(missing_ok=True)


class Updater:
    def __init__(self, folder, updates, settings, index=index_folder, graph_builder=build):
        self.folder, self.root = Path(folder).resolve(), Path(updates).resolve()
        if self.root.is_relative_to(self.folder) or self.folder.is_relative_to(self.root):
            raise ValueError("Keep --updates and --folder in separate, non-nested directories")
        manifest_path = self.root / "current.json"
        if manifest_path.exists():
            owner = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(owner, dict) or owner.get("corpus") != str(self.folder):
                raise ValueError("Update directory belongs to a different corpus; choose a separate --updates directory")
        self.settings, self.index, self.graph_builder = settings, index, graph_builder
        self.settings_hash = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
        self.failed = None
        self.observed, self.observed_since = None, None

    def status(self, phase, **fields):
        atomic_json(self.root / "status.json", {"corpus": str(self.folder), "phase": phase,
                                               "updated_at": now(), **fields})

    def current_matches(self, fingerprint):
        if not (self.root / "current.json").exists():
            return False
        manifest, _, _ = read_current(self.root, self.folder)
        return manifest["corpus_sha256"] == fingerprint and manifest.get("settings_sha256") == self.settings_hash

    def rebuild(self, fingerprint):
        generation = uuid.uuid4().hex
        directory = self.root / "generations" / generation
        self.status("building", generation=generation)
        try:
            directory.mkdir(parents=True)
            docs = load_corpus_documents(self.folder)  # Extract once for BOTH artifacts.
            if corpus_fingerprint(self.folder) != fingerprint:
                raise ValueError("Sources changed during extraction; wait for files to settle")
            collection = get_collection(str(directory / "db"))
            count = self.index(collection, self.folder, self.settings["vector_chunk_size"],
                               self.settings["vector_overlap"], documents=docs, id_prefix=generation + ":")
            graph = self.graph_builder(self.folder, directory / "graph.json", model=self.settings["model"],
                chunk_size=self.settings["graph_chunk_size"], overlap=self.settings["graph_overlap"],
                max_output_tokens=self.settings["max_output_tokens"], thinking=self.settings["thinking"],
                thinking_budget=self.settings["thinking_budget"], documents=docs,
                cache_dir=self.root / ".graph_cache", allow_empty=True)
            if graph["corpus_sha256"] != fingerprint or corpus_fingerprint(self.folder) != fingerprint:
                raise ValueError("Sources changed during the build; incomplete generation will not be published")
            manifest = {"version": 1, "generation": generation, "corpus": str(self.folder),
                        "corpus_sha256": fingerprint, "settings_sha256": self.settings_hash,
                        "published_at": now(), "indexed_chunks": count,
                        "relationships": len(graph["relationships"])}
            # Readers discover BOTH artifacts through this single atomic replacement.
            atomic_json(self.root / "current.json", manifest)
            self.failed = None
            self.status("ready", generation=generation, indexed_chunks=count,
                        relationships=len(graph["relationships"]))
            print(f"Published {generation}: {count} chunks, {len(graph['relationships'])} relationships.", flush=True)
            return True
        except Exception as exc:
            self.failed = fingerprint
            self.status("error", generation=generation, error=_safe_error(exc))
            print(f"Update failed: {_safe_error(exc)}. Previous published generation retained. "
                  "This source version will not be retried until files change or the updater restarts.", flush=True)
            return False

    def tick(self, timestamp, settle_seconds):
        try:
            fingerprint = corpus_fingerprint(self.folder)
        except (OSError, ValueError) as exc:
            self.status("error", error=_safe_error(exc))
            self.observed, self.observed_since = None, None
            return None
        if fingerprint != self.observed:
            self.observed, self.observed_since = fingerprint, timestamp
            return None
        if timestamp - self.observed_since < settle_seconds or self.failed == fingerprint:
            return None
        if self.current_matches(fingerprint):
            return None
        return self.rebuild(fingerprint)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=Path("prepared_context"))
    parser.add_argument("--updates", type=Path, default=Path(".context_updates"))
    parser.add_argument("--once", action="store_true", help="Build if changed, then exit; do not watch")
    parser.add_argument("--force", action="store_true", help="With --once, publish again even if unchanged; graph cache still applies")
    parser.add_argument("--poll-seconds", type=positive_int, default=2)
    parser.add_argument("--settle-seconds", type=positive_int, default=3)
    parser.add_argument("--vector-chunk-size", type=positive_int, default=600)
    parser.add_argument("--vector-overlap", type=int, default=80)
    parser.add_argument("--graph-chunk-size", type=positive_int, default=6000)
    parser.add_argument("--graph-overlap", type=int, default=300)
    parser.add_argument("--model", default=DEFAULT_MODELS["gemini"])
    parser.add_argument("--max-output-tokens", type=positive_int, default=8192)
    parser.add_argument("--gemini-thinking", choices=["auto", "low", "medium", "high", "provider-default"], default="auto")
    parser.add_argument("--gemini-thinking-budget", type=int)
    args = parser.parse_args()
    if args.force and not args.once:
        parser.error("--force requires --once")
    for prefix in ("vector", "graph"):
        if not 0 <= getattr(args, prefix + "_overlap") < getattr(args, prefix + "_chunk_size"):
            parser.error(f"Require 0 <= {prefix}-overlap < {prefix}-chunk-size")
    settings = {k: getattr(args, k) for k in ("vector_chunk_size", "vector_overlap", "graph_chunk_size",
                                             "graph_overlap", "model", "max_output_tokens")}
    settings.update(thinking=args.gemini_thinking, thinking_budget=args.gemini_thinking_budget)
    try:
        gemini_thinking_config(args.model, args.gemini_thinking, args.gemini_thinking_budget)
        updater = Updater(args.folder, args.updates, settings)
        # Validate before acquiring a lock; a missing folder is not an empty corpus.
        corpus_fingerprint(updater.folder)
        with writer_lock(updater.root):
            if args.once:
                fingerprint = corpus_fingerprint(updater.folder)
                if not args.force and updater.current_matches(fingerprint):
                    print("Prepared corpus and settings unchanged; no model calls or rebuild needed.")
                    return 0
                return 0 if updater.rebuild(fingerprint) else 1
            print(f"Watching {updater.folder}; Ctrl+C stops. Changes may call Gemini automatically. "
                  f"Polling every {args.poll_seconds}s, settling for {args.settle_seconds}s.", flush=True)
            while True:
                updater.tick(time.monotonic(), args.settle_seconds)
                time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        print("Updater stopped.")
        return 0
    except Exception as exc:
        print(f"Updater failed: {_safe_error(exc)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
