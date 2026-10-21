"""Automatic publication tests: real Chroma/MCP, mocked local embeddings and Gemini."""
import asyncio
from functools import partial
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from build_graph import build
from graph_context import corpus_fingerprint
from level2_vector_rag import index_folder
from level6_auto_update import Updater, writer_lock
from model_providers import Answer
from update_store import LiveCorpusTools, read_current

SETTINGS = {"vector_chunk_size": 600, "vector_overlap": 80, "graph_chunk_size": 6000,
            "graph_overlap": 300, "model": "gemini-3.8-flash", "max_output_tokens": 8192,
            "thinking": "auto", "thinking_budget": None}


def fake_generate(*args, **kwargs):
    sources = json.loads(args[2].split("EXCERPTS:\n")[1])
    edges = []
    for source in sources:
        subject, obj = source["text"].rstrip(".").split(" developed ")
        edges.append({"source_id": source["id"], "subject": subject, "relation": "developed",
                      "object": obj, "quote": source["text"]})
    return Answer(json.dumps({"relationships": edges}), "STOP", {}, "mock-gemini")


class AutoUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.folder = self.root / "prepared"
        self.folder.mkdir()
        self.note = self.folder / "note.txt"
        self.note.write_text("Ada developed Algorithm.")
        self.updates = self.root / "updates"
        self.generate = Mock(side_effect=fake_generate)
        self.builder = partial(build, generate=self.generate)
        self.updater = Updater(self.folder, self.updates, SETTINGS, graph_builder=self.builder)
        self.embed = patch("ollama.embed", return_value={"embeddings": [[1., 0., 0.]]}).start()
        self.addCleanup(patch.stopall)

    def publish(self, updater=None):
        self.assertTrue((updater or self.updater).rebuild(corpus_fingerprint(self.folder)))
        return read_current(self.updates, self.folder)[0]

    def test_debounce_ignores_unchanged_hidden_and_unsupported_files(self):
        self.assertIsNone(self.updater.tick(0, 3))
        self.assertIsNone(self.updater.tick(2, 3))
        self.note.write_text("Grace developed Compiler.")
        self.assertIsNone(self.updater.tick(3, 3))
        self.assertIsNone(self.updater.tick(5, 3))
        self.assertTrue(self.updater.tick(6, 3))
        manifest = read_current(self.updates, self.folder)[0]
        self.note.touch()
        (self.folder / ".hidden.txt").write_text("ignored")
        (self.folder / "ignored.json").write_text("{}")
        self.assertIsNone(self.updater.tick(20, 3))
        self.assertEqual(manifest, read_current(self.updates, self.folder)[0])
        self.assertEqual(self.generate.call_count, 1)

    def test_add_edit_delete_and_empty_corpus_reload(self):
        first = self.publish()
        live = LiveCorpusTools(self.folder, self.updates)
        self.assertEqual(live.get_corpus_status()["indexed_chunks"], 1)
        nested = self.folder / "nested"
        nested.mkdir()
        second_note = nested / "note.txt"
        second_note.write_text("Grace developed Compiler.")
        second = self.publish()
        self.assertNotEqual(first["generation"], second["generation"])
        self.assertEqual(live.get_corpus_status()["indexed_chunks"], 2)
        self.note.write_text("Lin developed Tool.")
        self.publish()
        result = live.get_relationships()
        self.assertEqual({e["subject"] for e in result["relationships"]}, {"Lin", "Grace"})
        self.note.unlink()
        self.publish()
        self.assertEqual(live.list_sources()["sources"][0]["source"], "nested/note.txt")
        second_note.unlink()
        calls = self.generate.call_count
        self.publish()
        status = live.get_corpus_status()
        self.assertTrue(status["ready"])
        self.assertTrue(status["graph"]["ready"])
        self.assertEqual(status["indexed_chunks"], 0)
        self.assertEqual(live.get_relationships()["relationships"], [])
        self.assertEqual(self.generate.call_count, calls)

    def test_failure_keeps_previous_pair_and_does_not_retry_every_poll(self):
        first = self.publish()
        self.note.write_text("Grace developed Compiler.")
        failing = Mock(side_effect=RuntimeError("Gemini unavailable"))
        updater = Updater(self.folder, self.updates, SETTINGS, graph_builder=failing)
        self.assertIsNone(updater.tick(0, 3))
        self.assertFalse(updater.tick(3, 3))
        self.assertIsNone(updater.tick(30, 3))
        self.assertEqual(failing.call_count, 1)
        self.assertEqual(first, read_current(self.updates, self.folder)[0])
        live = LiveCorpusTools(self.folder, self.updates)
        result = live.get_relationships()
        self.assertEqual(result["relationships"][0]["subject"], "Ada")
        self.assertEqual(result["snapshot"]["freshness"], "stale")
        self.assertEqual(result["snapshot"]["updater"]["phase"], "error")
        self.publish()  # A new/manual attempt can recover after the dependency is fixed.

    def test_source_change_during_build_never_publishes_mixed_pair(self):
        first = self.publish()
        self.note.write_text("Grace developed Compiler.")
        def changing_index(*args, **kwargs):
            count = index_folder(*args, **kwargs)
            self.note.write_text("Lin developed Tool.")
            return count
        updater = Updater(self.folder, self.updates, SETTINGS, index=changing_index, graph_builder=self.builder)
        self.assertFalse(updater.rebuild(corpus_fingerprint(self.folder)))
        self.assertEqual(first, read_current(self.updates, self.folder)[0])

    def test_lock_config_scope_missing_folder_and_cache_reuse(self):
        with writer_lock(self.updates):
            with self.assertRaisesRegex(ValueError, "lock exists"):
                with writer_lock(self.updates):
                    pass
        self.assertFalse((self.updates / "writer.lock").exists())
        self.publish()
        calls = self.generate.call_count
        self.publish()
        self.assertEqual(self.generate.call_count, calls)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            read_current(self.updates, self.root / "different")
        with self.assertRaisesRegex(ValueError, "non-nested"):
            Updater(self.folder, self.folder / "output", SETTINGS)
        self.note.unlink()
        self.folder.rmdir()
        self.assertIsNone(self.updater.tick(10, 3))
        self.assertEqual(LiveCorpusTools(self.folder, self.updates).get_corpus_status()["snapshot"]["freshness"], "source unavailable")

    def test_cli_reads_published_pair_and_prevents_index_writes(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        import level2_vector_rag
        import level4_hybrid_rag
        self.publish()
        common = ["demo", "--folder", str(self.folder), "--updates", str(self.updates)]
        with patch.object(sys, "argv", common + ["--index-only"]), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                level2_vector_rag.main()
            self.assertEqual(error.exception.code, 2)
        with patch.object(sys, "argv", common + ["--query", "Who developed Algorithm?"]), \
                patch("level4_hybrid_rag.run_answers", return_value=0) as answer, redirect_stdout(io.StringIO()):
            self.assertEqual(level4_hybrid_rag.main(), 0)
            self.assertIn("Ada developed Algorithm.", answer.call_args.args[0])
        with self.assertRaisesRegex(ValueError, "different corpus"):
            Updater(self.root / "other", self.updates, SETTINGS)

    def test_running_mcp_process_follows_new_generation_without_restart(self):
        first = self.publish()
        async def check():
            params = StdioServerParameters(command=sys.executable, args=[
                str(Path(__file__).parent / "level5_mcp_server.py"), "--folder", str(self.folder),
                "--updates", str(self.updates)])
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    before = await session.call_tool("get_corpus_status", {})
                    self.assertEqual(before.structuredContent["snapshot"]["generation"], first["generation"])
                    _, db, _ = read_current(self.updates, self.folder)
                    from corpus_tools import CorpusTools
                    old_id = CorpusTools(self.folder, db).metadata()["ids"][0]
                    self.note.write_text("Grace developed Compiler.")
                    second = self.publish()
                    after = await session.call_tool("get_corpus_status", {})
                    self.assertEqual(after.structuredContent["snapshot"]["generation"], second["generation"])
                    graph = await session.call_tool("get_relationships", {"entity": "Grace"})
                    self.assertEqual(graph.structuredContent["relationships"][0]["subject"], "Grace")
                    old_hit = await session.call_tool("fetch_source_excerpt", {"chunk_id": old_id})
                    self.assertTrue(old_hit.isError)
        asyncio.run(asyncio.wait_for(check(), 30))


if __name__ == "__main__":
    unittest.main()
