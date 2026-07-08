import unittest

from scripts.eval import _normalize_dataset


class EvaluationDatasetTests(unittest.TestCase):
    def test_dataset_labels_are_normalized_with_non_duplicate_acceptables(self):
        dataset = _normalize_dataset("data/evaluation_dataset50.json")

        self.assertTrue(dataset)
        for sample in dataset:
            expected_documents = sample.get("expected_documents") or []
            acceptable_documents = sample.get("acceptable_documents") or []

            self.assertTrue(expected_documents)
            self.assertTrue(acceptable_documents)
            self.assertNotEqual(expected_documents, acceptable_documents)


if __name__ == "__main__":
    unittest.main()
