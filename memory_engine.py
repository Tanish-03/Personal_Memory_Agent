from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class MemoryIntentClassifier:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-large")
        self.model = AutoModelForSequenceClassification.from_pretrained("microsoft/deberta-v3-large")

    def classify_intent(self, text):
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,       # ✅ Prevents overflow
            max_length=512         # ✅ Ensures model compatibility
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits).item()
        return predicted_class
