import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Retrieve environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")
PINECONE_NAMESPACE = "ZOHO_Analytics"  # Set namespace directly here

# Folder containing vector data in JSON format
CHUNK_FOLDER = "./Chunks"

# Function to load vectors from JSON files in the folder
def load_vectors_from_folder(folder_path):
    vectors = []
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if file_name.endswith(".json"):  # Ensure it's a JSON file
            with open(file_path, "r", encoding="utf-8") as f:  # Use UTF-8 encoding
                data = json.load(f)  # Load JSON content
                for item in data:
                    if 'id' not in item or 'embedding' not in item:
                        raise ValueError("Each vector must have an 'id' and 'embedding' field.")
                    
                    # Prepare vector for upsert
                    vector = {
                        "id": str(item["id"]),  # Ensure the id is a string
                        "values": item["embedding"],  # Use the embedding values
                        "metadata": item.get("metadata", {})  # Include metadata if present
                    }
                    vectors.append(vector)
    return vectors

# Load vectors from the chunk folder
vectors = load_vectors_from_folder(CHUNK_FOLDER)

# Construct the request URL
url = f"{PINECONE_INDEX_HOST}/vectors/upsert"

# Prepare the request headers
headers = {
    "Api-Key": PINECONE_API_KEY,
    "Content-Type": "application/json",
    "X-Pinecone-API-Version": "2024-07",
}

# Prepare the request body with the namespace added
data = {
    "namespace": PINECONE_NAMESPACE,  # Include the namespace here
    "vectors": vectors
}

# Send the upsert request to Pinecone
response = requests.post(url, headers=headers, json=data)

# Check the response status
if response.status_code == 200:
    print(f"Successfully upserted {len(vectors)} vectors into Pinecone.")
else:
    print(f"Failed to upsert vectors. Status code: {response.status_code}, Message: {response.text}")
