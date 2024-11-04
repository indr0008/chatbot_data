import os

# Access environment variables
# llm_endpoint = os.environ["AZURE_OPENAI_LLM_ENDPOINT"]
# https://openai-edasquad4.openai.azure.com/
# embedding_endpoint = os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"]
# https://openai-edasquad4.openai.azure.com/openai/deployments/mitav22_bydani/embeddings?api-version=2024-05-13
# azure_openai_version = os.environ['AZURE_OPENAI_VERSION']
# 2024-05-13
# api_key = os.environ['AZURE_OPENAI_API_KEY']
# 11cbd8db120f43879b22fc632258ecbc

# AZURE_OPENAI_EMBEDDING_ENDPOINT = "https://openai-edasquad1.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15"

# AZURE_OPENAI_API_KEY= "d7fd42addeff4f4a91f9beea8996f4cc"

# AZURE_OPENAI_LLM_ENDPOINT = "https://openai-edasquad1.openai.azure.com/openai/deployments/gpt-4o-mini-4/chat/completions?api-version=2024-08-01-preview"

# AZURE_OPENAI_VERSION = "2024-08-01-preview"

llm_endpoint = os.getenv("AZURE_OPENAI_LLM_ENDPOINT","https://openai-edasquad1.openai.azure.com/openai/deployments/gpt-4o-mini-4/chat/completions?api-version=2024-08-01-preview")

embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT","https://openai-edasquad1.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15")

azure_openai_version = os.getenv('AZURE_OPENAI_VERSION',"2024-08-01-preview")

api_key = os.getenv('AZURE_OPENAI_API_KEY',"d7fd42addeff4f4a91f9beea8996f4cc")


vector_store_name = os.getenv('VECTOR_STORE_NAME', 'VS-final')
low_temp_param = float(os.getenv('LOW_TEMP_PARAM', 0.3))
high_temp_param = float(os.getenv('HIGH_TEMP_PARAM', 0.4))


similarity_search_k= int(os.getenv('SIMILARITY_SEARCH_K', 5))
similarity_search_threshold = float(os.getenv('SIMILARITY_SEARCH_THRESHOLD', 0.65))
similarity_search_alpha = float(os.getenv('SIMILARITY_SEARCH_ALPHA', 0.7))