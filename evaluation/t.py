import json
import pandas as pd
from pathlib import Path
from abc import ABC, abstractmethod
from google import genai
from openai import OpenAI
import time
import random
import os
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

# ---------------------- API KEYS ----------------------
OPENROUTE_API_KEY = os.environ.get("OPENROUTE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Check if the required key is present
if not OPENROUTE_API_KEY:
    raise ValueError("OPENROUTE_API_KEY not found in .env file. Please add it.")


Evaluator_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTE_API_KEY,
)


gemini_client = genai.Client(api_key = GEMINI_API_KEY)

# ---------------------- FILE UTILS ----------------------
queries_path = "queries.json"

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
                if not all(k in item for k in ['query', 'ground_truth']):
                    raise ValueError(f"JSON item missing fields: {item}")
            return data
    elif file_type == 'csv':
        df = pd.read_csv(file_path)
        required_cols = [ 'query', 'ground_truth']
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

    def chat(self, query: str) -> str:
        messages = [
            {"role": "system", "content": "You are a factual QA assistant. Use the most up-to-date information. Respond concisely with a single factual answer. If unknown, reply 'Unknown'."},
            {"role": "user", "content": query}
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0
        )
        return response.choices[0].message.content.strip()

class GeminiAdapter(LLMClient):
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def chat(self, query: str, max_retries=5) -> str:
        contents = [
            "You are a factual QA assistant. Respond concisely with a single factual answer.",
            f"Question: {query}"
        ]

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents
                )
                return response.text.strip()
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    print(f"⚠️ {self.model} overloaded. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise e
        raise RuntimeError(f"Max retries reached for {self.model}")

# ---------------------- INITIALIZE MODEL CLIENTS ----------------------
model_clients = {
    #"gemma-2-9b-it": OpenAICompatibleClient(openroute_client, "google/gemma-2-9b-it"),
    #"deepseek-r1t2-chimera" : OpenAICompatibleClient(openroute_client, "tngtech/deepseek-r1t2-chimera:free"),
    #"lemma-3.3-8b": OpenAICompatibleClient(openroute_client, "meta-llama/llama-3.3-8b-instruct:free"),
    #"gemini-2.0-flash" : GeminiAdapter(gemini_client, "gemini-2.0-flash-exp"),
    "nemotron-nano-9b-v2": OpenAICompatibleClient(openroute_client, "nvidia/nemotron-nano-9b-v2:free"),
}

# ---------------------- BENCHMARK LOOP ----------------------
def benchmark(model_clients, queries):
    def run_model(name, client):
        print(f"Running {name}...")
        model_responses = []
        for q in queries:
            ans = client.chat(q["query"])
            model_responses.append({
                "query": q["query"],
                "response": ans,
                "ground_truth": q["ground_truth"],
            })

        safe_name = name.replace("-", "_")
        output_file = f"./responses/{safe_name}.json"
        Save_Responses(model_responses, output_file)
        print(f"✅ Saved: {output_file}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_clients)) as executor:
        futures = {executor.submit(run_model, name, client): name for name, client in model_clients.items()}

        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"❌ Error in {name}: {e}")
    print("✅ Saved: all_models_responses.json")

# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    try:
        queries = read_queries(queries_path)
        os.makedirs("responses", exist_ok=True)
        benchmark(model_clients, queries)
    except Exception as e:
        print(f"Error: {e}")
