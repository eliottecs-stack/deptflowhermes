from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deptflow_sdr.control_plane.llm import HeuristicProvider, OpenAIProvider, make_llm_provider


class LLMProviderTest(unittest.TestCase):
    def test_openai_is_default_provider_when_api_key_exists(self):
        provider = make_llm_provider({"OPENAI_API_KEY": "sk-test", "OPENAI_MODEL": "gpt-4.1-mini"})
        self.assertIsInstance(provider, OpenAIProvider)
        self.assertEqual(provider.model, "gpt-4.1-mini")
        self.assertNotIn("sk-test", repr(provider))

    def test_heuristic_provider_is_safe_fallback_without_key(self):
        provider = make_llm_provider({})
        self.assertIsInstance(provider, HeuristicProvider)
        result = provider.generate_json("Transforme cet ICP", {"roles": ["CEO"]})
        self.assertEqual(result["provider"], "heuristic")
        self.assertEqual(result["input"]["roles"], ["CEO"])


if __name__ == "__main__":
    unittest.main()
