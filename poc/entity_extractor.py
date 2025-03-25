from typing import List

import spacy


class EntityExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            import subprocess

            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

    def extract_entities(self, text: str) -> List[str]:
        doc = self.nlp(text)
        entities = [ent.text for ent in doc.ents]

        entities.extend([chunk.text for chunk in doc.noun_chunks])

        normalized_entities = []
        for entity in entities:
            normalized = entity.lower().strip()
            if normalized and normalized not in normalized_entities:
                normalized_entities.append(normalized)

        return normalized_entities


extractor = EntityExtractor()
texts = [
    "The quick brown fox jumps over the lazy dog.",
    "What is the capital of France?",
    "Who is the president of the United States?",
    "Please remind me to buy milk at 5 PM.",
    "How many times do a human's heart beat in a day?",
]

for text in texts:
    entities = extractor.extract_entities(text)
    print(f"Entities in '{text}': {entities}")
