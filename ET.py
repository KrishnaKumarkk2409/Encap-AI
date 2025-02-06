import os
import time
import json
import openai
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import tiktoken
import csv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("Error: OPENAI_API_KEY not found in environment variables")
    exit(1)

# Use the fixed CSV file name "KB.csv"
csv_filename = "KB.csv"

# Read the CSV file
try:
    df = pd.read_csv(csv_filename)
    # Convert DataFrame to list of dictionaries and ensure all required columns exist
    required_columns = ['Root Node', 'Root Link', 'P1 Name', 'P1 Link', 
                        'P2 Name', 'P2 Link', 'P3 Name', 'P3 Link',
                        'P4 Name', 'P4 Link', 'Leaf name', 'Leaf Link']
    
    print("Available columns in CSV:", df.columns.tolist())
    
    if not all(col in df.columns for col in required_columns):
        print("Error: CSV file is missing required columns. Please ensure all required columns exist:")
        print(required_columns)
        exit(1)
        
    leaf_data = df[required_columns].to_dict('records')
except FileNotFoundError:
    print(f"Error: File '{csv_filename}' not found in the current directory.")
    exit(1)
except Exception as e:
    print(f"Error reading CSV file: {e}")
    exit(1)

# Set up headless browser options
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--remote-debugging-port=9222')

# Initialize the browser with service
service = Service()
driver = webdriver.Chrome(options=chrome_options)

# Function to scrape text from a given URL
def scrape_text(url):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            driver.get(url)
            time.sleep(10)  # Allow time for the page to load
            
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'ArticleDetailLeftContainer__box'))
                )
            except TimeoutException:
                print(f"Warning: Timeout waiting for content on {url}, retrying...")
                driver.refresh()
                time.sleep(5)
                continue
            except WebDriverException as e:
                print(f"WebDriver error: {e}")
                time.sleep(10)
                continue
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            main_content = soup.find('div', {'class': 'ArticleDetailLeftContainer__box'})
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
                if text.strip():
                    return text
            print(f"Warning: No content found for {url}, retrying...")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(10)
    return None  # If all attempts fail, return None

def chunk_text_by_tokens(text, max_tokens=7000):
    if not text or not isinstance(text, str):
        print("Warning: Invalid text input for chunking")
        return []
    
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    chunks = []

    start = 0
    end = max_tokens
    while start < len(tokens):
        token_chunk = tokens[start:end]
        chunk_text = tokenizer.decode(token_chunk)
        chunks.append(chunk_text)
        start += max_tokens
        end += max_tokens

    return chunks

def embed_text_openai(text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response["data"][0]["embedding"]
        except openai.error.RateLimitError:
            if attempt == max_retries - 1:
                print("Rate limit reached, failing after max retries")
                return None
            print("Rate limit reached, waiting 60 seconds...")
            time.sleep(60)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

def save_embeddings_to_json(embeddings, file_count):
    folder_path = "Chunks"
    os.makedirs(folder_path, exist_ok=True)
    file_name = f"embeddings_batch_{file_count}.json"
    file_path = os.path.join(folder_path, file_name)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(embeddings, json_file, ensure_ascii=False, indent=4)
        print(f"Saved {len(embeddings)} embeddings to {file_path}")
    except Exception as e:
        print(f"Error saving embeddings to JSON: {e}")

# Create CSV file to log errors with leaf details
def create_error_log_file():
    error_log_filename = 'scraping_errors.csv'
    if not os.path.exists(error_log_filename):
        with open(error_log_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Root Node', 'Root Link', 'P1 Name', 'P1 Link', 'P2 Name', 'P2 Link',
                             'P3 Name', 'P3 Link', 'P4 Name', 'P4 Link', 'Leaf Name', 'Leaf Link', 'Error'])
    return error_log_filename

def log_error_to_csv(error_log_filename, leaf_data, error_message):
    try:
        with open(error_log_filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([leaf_data['Root Node'], leaf_data['Root Link'], leaf_data['P1 Name'], leaf_data['P1 Link'],
                             leaf_data['P2 Name'], leaf_data['P2 Link'], leaf_data['P3 Name'], leaf_data['P3 Link'],
                             leaf_data['P4 Name'], leaf_data['P4 Link'], leaf_data['Leaf name'], leaf_data['Leaf Link'], error_message])
        print(f"Logged error for {leaf_data['Leaf name']} to {error_log_filename}")
    except Exception as e:
        print(f"Error writing to error log file: {e}")
def get_processed_leaves():
    processed_leaves = set()
    log_filename = 'processing_log.csv'
    if os.path.exists(log_filename):
        try:
            log_df = pd.read_csv(log_filename)
            successful_leaves = log_df[
                (log_df['Chunk Status'] == 'YES') & 
                (log_df['Embedding Status'] == 'YES')
            ]
            processed_leaves = set(successful_leaves['Leaf Link'].tolist())
        except Exception as e:
            print(f"Error reading log file: {e}")
    return processed_leaves

def scrape_chunk_and_embed(leaf_data):
    total_leaves = len(leaf_data)
    print(f"Starting processing of {total_leaves} leaves...")
    
    embeddings_batch = []
    batch_size = 50
    file_count = 1
    id_counter = 1
    error_log_filename = create_error_log_file()

    # Get the last successful ID from existing JSON files
    last_id = get_last_processed_id()
    if last_id:
        id_counter = last_id + 1
        file_count = (last_id // batch_size) + 1

    # Get already processed leaves
    processed_leaves = get_processed_leaves()
    print(f"Found {len(processed_leaves)} already processed leaves")

    idx = 0
    while idx < len(leaf_data):
        leaf = leaf_data[idx]
        leaf_link = leaf.get('Leaf Link')
        
        # Skip already processed leaves
        if leaf_link in processed_leaves:
            print(f"Skipping already processed leaf: {leaf.get('Leaf name')}")
            idx += 1
            continue

        print(f"Processing leaf {idx + 1} of {total_leaves} ({((idx+1)/total_leaves)*100:.1f}%)")
        
        # Get all metadata from the current leaf record
        leaf_name = leaf.get('Leaf name')
        root_name = leaf.get('Root Node')
        root_link = leaf.get('Root Link')
        p1_name = leaf.get('P1 Name')
        p1_link = leaf.get('P1 Link')
        p2_name = leaf.get('P2 Name')
        p2_link = leaf.get('P2 Link')
        p3_name = leaf.get('P3 Name')
        p3_link = leaf.get('P3 Link')
        p4_name = leaf.get('P4 Name')
        p4_link = leaf.get('P4 Link')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if leaf_link and leaf_link != 'No Leaf Link':
            success = False
            while not success:
                print(f"Scraping data from: {leaf_link}")
                scraped_text = scrape_text(leaf_link)

                if scraped_text:
                    chunks = chunk_text_by_tokens(scraped_text, max_tokens=7000)
                    print(f"Data for {leaf_name} broken into {len(chunks)} chunks.")
                    chunk_status = "YES"
                    
                    for chunk in chunks:
                        embedding = None
                        while embedding is None:
                            embedding = embed_text_openai(chunk)
                            if embedding is None:
                                print("Failed to get embedding, retrying after 60 seconds...")
                                time.sleep(60)
                        
                        embeddings_batch.append({
                            "id": id_counter,
                            "combined_chunk": f"Root: {root_name}\nP1: {p1_name}\nP2: {p2_name}\nP3: {p3_name}\nP4: {p4_name}\nLeaf: {leaf_name}\nChunk: {chunk}",
                            "embedding": embedding,
                            "metadata": {
                                "root_name": root_name,
                                "root_link": root_link,
                                "p1_name": p1_name,
                                "p1_link": p1_link,
                                "p2_name": p2_name,
                                "p2_link": p2_link,
                                "p3_name": p3_name,
                                "p3_link": p3_link,
                                "p4_name": p4_name,
                                "p4_link": p4_link,
                                "leaf_name": leaf_name,
                                "leaf_link": leaf_link
                            }
                        })
                        id_counter += 1

                        if len(embeddings_batch) >= batch_size:
                            save_embeddings_to_json(embeddings_batch, file_count)
                            file_count += 1
                            embeddings_batch = []
                    
                    success = True
                    log_to_csv(log_filename, leaf_name, leaf_link, chunk_status, "YES", len(chunks), timestamp)
                else:
                    print(f"Failed to scrape {leaf_link}, logging error...")
                    log_error_to_csv(error_log_filename, leaf, "Scraping failed or timed out")
                    time.sleep(30)
        
        idx += 1

    if embeddings_batch:
        save_embeddings_to_json(embeddings_batch, file_count)

def get_last_processed_id():
    folder_path = "Chunks"
    if not os.path.exists(folder_path):
        return None
    
    last_id = 0
    for filename in os.listdir(folder_path):
        if filename.startswith("embeddings_batch_") and filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:
                        last_id = max(last_id, max(item["id"] for item in data))
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return last_id if last_id > 0 else None

# Main execution
try:
    scrape_chunk_and_embed(leaf_data)
finally:
    driver.quit()
    print("Browser session closed successfully")
