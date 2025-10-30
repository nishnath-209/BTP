# using LLM as judhe for evaluation
# choosen LLM is gpt-oss-20b
from openai import OpenAI
import json
from pathlib import Path
import pandas as pd
from abc import ABC, abstractmethod
import re
import os
import concurrent.futures

# ---------------------- API KEYS ----------------------
keys = {
    'gemini': "AIzaSyAsoJ9X12EmXaus1kPiCXnN99KI-iQsEFA",
    'openroute': "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"
}

Evaluator_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key= keys['openroute'],
)


# ---------------------- FILE UTILS ----------------------
models = [#"deepseek_r1t2_chimera","gemini_2.0_flash","gemma_2_9b_it","lemma_3.3_8b",
          "nemotron_nano_9b_v2"]

def detect_file_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == '.json':
        try:
            with open(file_path, 'r') as f:
                json.load(f)
                return 'json'
        except:
            pass
    elif ext == '.csv':
        try:
            pd.read_csv(file_path, nrows=1)
            return 'csv'
        except:
            pass
    raise ValueError(f"File {file_path} is neither valid JSON nor CSV")

def read_queries(file_path: str) -> list:
    file_type = detect_file_type(file_path)
    if file_type == 'json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                if not all(k in item for k in ['query','response', 'ground_truth']):
                    raise ValueError(f"JSON item missing fields: {item}")
            return data
    elif file_type == 'csv':
        df = pd.read_csv(file_path)
        required_cols = [ 'query', 'response','ground_truth']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV missing required columns: {required_cols}")
        return df[required_cols].to_dict('records')

def Save_Responses(responses: list, output_path: str):
    with open(output_path, 'w') as f:
        json.dump(responses, f, indent=4)



# ---------------------- LLM INTERFACE ----------------------

class LLMClient(ABC):
    @abstractmethod
    def chat(self, query: str) -> str:
        pass

class OpenAICompatibleClient(LLMClient):
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def chat(self,query:str, LLM_Resp: str, Ground_truth: str) -> float:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert evaluator model. "
                    "Given a user query, a ground truth answer, and an LLM-generated response, "
                    "compare their meanings and output a similarity score between 0 and 1. "
                    "You must consider semantic equivalence, abbreviations, and entity synonyms "
                    "(e.g., 'USA' = 'United States', 'UK' = 'United Kingdom'). "
                    "Scoring rules:\n"
                    "- If both responses mean the same thing, output 1.\n"
                    "- If numeric, compute score = 1 - (|predicted - true| / max(|true|, 1)), clamped to [0,1].\n"
                    "- For partially correct or semantically close answers, use a value in (0,1).\n"
                    "- Output only the numeric score, no text or explanation."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Query: {query}\n"
                    f"Ground truth: {Ground_truth}\n"
                    f"LLM response: {LLM_Resp}\n\n"
                    "Return only the numeric similarity score between 0 and 1."
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
        )

        content = response.choices[0].message.content.strip()

        # Extract numeric score using regex (handles cases like "Score: 0.87")
        match = re.search(r"[-+]?\d*\.\d+|\d+", content)
        if match:
            score = float(match.group())
            return max(0.0, min(1.0, score))
        else:
            raise ValueError(f"Could not extract numeric score from response: {content}")


evaluator = OpenAICompatibleClient(Evaluator_client, "openai/gpt-oss-20b:free")

def score_response(queries : list) -> list:
    scored_responses = []
    for item in queries:
        llm_response = item['response']
        ground_truth = item['ground_truth']
        score = evaluator.chat(item['query'],llm_response, ground_truth)
        scored_responses.append({
            "query": item['query'],
            "response": llm_response,
            "ground_truth": ground_truth,
            "score": score
        })
    return scored_responses

def process_model(model_name):
    try:
        path = f"./responses/{model_name}.json"
        queries = read_queries(path)
        scores = score_response(queries)

        score_file = f"./scores/{model_name}.json"
        Save_Responses(scores, score_file)
        print(f"✅ Saved: {score_file}")
    except Exception as e:
        print(f"❌ Error in {model_name}: {e}")

if __name__ == "__main__":
    os.makedirs("scores", exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(models)) as executor:
        executor.map(process_model, models)