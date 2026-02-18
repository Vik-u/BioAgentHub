import os
import unittest

from services import local_llm


class TestLLMIntegration(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("USE_REAL_LLM") == "1", "requires USE_REAL_LLM=1")
    def test_real_llm_generate(self):
        if local_llm.BACKEND in {"openai", "azure-openai"}:
            key_env = local_llm.CONFIG.get("api_key_env", "OPENAI_API_KEY")
            if not os.environ.get(key_env):
                self.fail(f"Missing {key_env} for real LLM integration test")
        text = local_llm.generate("Reply with the single word: ping")
        self.assertTrue(text)


if __name__ == "__main__":
    unittest.main()
