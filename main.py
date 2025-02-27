from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time
import psycopg2
from dotenv import load_dotenv
import os
import re
import threading
import json
from datetime import datetime
import sys
from pathlib import Path
import io
import logging

# Suppress transformers logs
logging.getLogger("transformers").setLevel(logging.ERROR)

# Check if .env file exists
env_path = Path('.env')
if not env_path.exists():
    print("❌ Error: .env file not found.")
    print("Please create a .env file with the following variables:")
    print("DB_HOST=your_host")
    print("DB_PORT=your_port")
    print("DB_NAME=your_database_name")
    print("DB_USER=your_username")
    print("DB_PASSWORD=your_password")
    sys.exit(1)

# Load environment variables from .env file
# This file should contain database connection details:
# DB_HOST: Database host address
# DB_PORT: Database port
# DB_NAME: Database name
# DB_USER: Database username
# DB_PASSWORD: Database password
load_dotenv()

# Check if required environment variables are set
required_env_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_PORT"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please make sure your .env file contains all required variables.")
    sys.exit(1)

# DB_CONFIG using only environment variables without defaults
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT")
}

# Cache directory for models - can be configured via environment variable
CACHE_DIR = os.getenv("CACHE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

# Capture HF transformers output and prevent it from interfering
class CaptureHFOutput:
    def __init__(self):
        self.original_stdout = sys.stdout
        self.output_buffer = io.StringIO()
    
    def __enter__(self):
        sys.stdout = self.output_buffer
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        # Print captured output without progress interaction
        print(self.output_buffer.getvalue().strip())

class Spinner:
    """Simple spinner context manager"""
    def __init__(self):
        self.running = False
        self.chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.thread = None
    
    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r\033[K")  # Clear the line
        sys.stdout.flush()
    
    def _spin(self):
        i = 0
        while self.running:
            sys.stdout.write(f"\rGenerating query... {self.chars[i]} ")
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(self.chars)

def load_model():
    """Load model with optimized settings for MPS (Apple Silicon)"""
    model_name = "defog/sqlcoder-7b-2"
    
    # Check if MPS is available
    mps_available = torch.backends.mps.is_available()
    if mps_available:
        print("Apple Silicon GPU (MPS) is available")
        device = "mps"
    else:
        print("⚠️ Apple Silicon GPU (MPS) is not available, falling back to CPU")
        device = "cpu"
    
    print(f"Using device: {device}")
    
    # For MPS, we'll use a different approach since bitsandbytes 4-bit doesn't work well with MPS
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=CACHE_DIR)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id
    
    print("Loading model (this may take a moment)...")
    start_time = time.time()
    
    try:
        # For MPS, we load with lower precision but without bitsandbytes
        if device == "mps":
            print("Using fp16 precision for MPS (Apple Silicon)...")
            with CaptureHFOutput():
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    cache_dir=CACHE_DIR,
                    device_map={"": device}  # Direct mapping to MPS
                )
                model.config.pad_token_id = tokenizer.pad_token_id
        else:
            # For CPU, try to use reduced precision to save memory
            print("Loading with reduced precision for CPU...")
            with CaptureHFOutput():
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,  # Regular precision for CPU
                    trust_remote_code=True,
                    cache_dir=CACHE_DIR,
                    low_cpu_mem_usage=True,
                    device_map="auto"
                )
                model.config.pad_token_id = tokenizer.pad_token_id
        
        load_time = time.time() - start_time
        
        # Show success message
        if device == "mps":
            print(f"Model loaded on Apple Silicon GPU in {load_time:.2f}s")
        else:
            print(f"Model loaded on CPU in {load_time:.2f}s")
        
        # Try to show memory usage
        try:
            memory_footprint = sum([param.numel() * param.element_size() for param in model.parameters()]) / 1024 / 1024
            print(f"Approximate memory usage: {memory_footprint:.2f} MB")
        except:
            pass
            
        return model, tokenizer
    
    except Exception as e:
        print(f"🚨 Model loading failed: {e}")
        print("⚠️ Trying with minimal configuration...")
        
        # Last resort: try with minimal config on CPU first
        try:
            print("Loading model with minimal config...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                cache_dir=CACHE_DIR,
                low_cpu_mem_usage=True
            )
            model.config.pad_token_id = tokenizer.pad_token_id
            
            # After loading, try to move to the requested device if not CPU
            if device != "cpu":
                try:
                    print(f"Moving model to {device}...")
                    model = model.to(device)
                except Exception as move_error:
                    print(f"⚠️ Failed to move to {device}, using CPU: {move_error}")
            
            print("Model loaded successfully with fallback method")
            return model, tokenizer
        except Exception as e2:
            print(f"All loading attempts failed: {e2}")
            sys.exit(1)

def optimize_schema(schema_text):
    """Optimize schema for better SQL generation."""
    if not schema_text:
        return "SCHEMA_NOT_FOUND"
    
    # Check if the schema is in the old format (just table definitions)
    if schema_text.startswith("event_categories(") or "FK:" in schema_text:
        # Convert to a more SQL-like format
        lines = schema_text.split('\n')
        tables = {}
        foreign_keys = []
        
        # First pass: collect table definitions
        for line in lines:
            if "(" in line and ")" in line and not line.startswith("FK:"):
                table_name = line.split("(")[0].strip()
                columns = line.split("(")[1].split(")")[0].strip()
                tables[table_name] = columns
            elif line.startswith("FK:"):
                foreign_keys.append(line)
        
        # Second pass: format as CREATE TABLE statements with constraints
        formatted_lines = []
        for table_name, columns in tables.items():
            formatted_lines.append(f"CREATE TABLE {table_name} ({columns});")
        
        # Add foreign key constraints as comments
        for fk in foreign_keys:
            parts = fk.split("→")
            if len(parts) == 2:
                fk_name = parts[0].strip().replace("FK: ", "")
                ref = parts[1].strip()
                formatted_lines.append(f"-- {fk_name} REFERENCES {ref}")
        
        schema_text = "\n".join(formatted_lines)
    
    # Truncate to 6000 characters to prevent token overflow
    # But try to keep complete statements by finding the last semicolon before the limit
    if len(schema_text) > 6000:
        truncated = schema_text[:6000]
        last_semicolon = truncated.rfind(';')
        if last_semicolon > 0:
            schema_text = truncated[:last_semicolon+1]
        else:
            schema_text = truncated
    
    return schema_text

def generate_sql(model, tokenizer, question, schema):
    """Generate SQL with optimized parameters for MPS and CPU"""
    start_time = time.time()
    
    # Create debug info with device information
    debug_info = {
        "model": "defog/sqlcoder-7b-2",
        "device": str(model.device),
        "is_gpu": "Yes" if "mps" in str(model.device) else "No"
    }
    
    # Format prompt with clear structure to help the model focus
    prompt = f"""### PostgreSQL Schema:
{schema}

### User Question:
{question}

### SQL Query (no table aliases):
"""
    
    # Tokenize with attention mask
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=1024,
        truncation=True,
        padding=True,
        return_attention_mask=True
    ).to(model.device)
    
    # Configure generation parameters
    # Simplify for MPS to prevent errors
    using_mps = "mps" in str(model.device)
    generation_config = {
        "max_new_tokens": 150,
        "num_beams": 1 if using_mps else 2,  # Simpler for MPS
        "do_sample": False,
        "early_stopping": not using_mps,  # Only enable when not using MPS
        "pad_token_id": tokenizer.pad_token_id,
    }
    
    if not using_mps:
        # Additional parameters for CPU only (may cause errors on MPS)
        generation_config.update({
            "repetition_penalty": 1.1,  # Avoid repetition
            "length_penalty": 1.0,  # Balanced length
        })
    
    # Generate with optimized config
    try:
        with torch.inference_mode():  # Use inference mode for memory efficiency
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                **generation_config
            )
    except Exception as e:
        debug_info["error"] = f"Generation error: {str(e)}"
        print(f"⚠️ Error during generation: {e}")
        # Fallback to simpler generation if error occurs
        try:
            print("Trying simpler generation parameters...")
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=100,
                pad_token_id=tokenizer.pad_token_id
            )
        except Exception as e2:
            debug_info["error"] = f"Fallback generation failed: {str(e2)}"
            return "", debug_info
    
    # Extract SQL from output
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    try:
        # Extract just the SQL part after the last "### SQL Query"
        if "### SQL Query" in full_output:
            sql_part = full_output.split("### SQL Query")[-1].strip()
            if sql_part.startswith("(no table aliases):"):
                sql_part = sql_part[len("(no table aliases):"):].strip()
        else:
            # Alternative extraction if marker isn't found
            sql_lines = [line for line in full_output.split("\n") if line.strip() and not line.startswith("#")]
            sql_part = "\n".join(sql_lines[-5:])  # Take the last 5 non-empty, non-comment lines
        
        # Clean up the SQL
        sql_part = sql_part.strip()
        if not sql_part.endswith(";"):
            sql_part += ";"
            
        # Remove any markdown code blocks
        sql_part = re.sub(r'```sql|```', '', sql_part).strip()
        
        # Ensure we're not returning the schema as SQL
        if sql_part.startswith("CREATE TABLE") or sql_part.startswith("event_categories(") or "FK:" in sql_part:
            # This is likely the schema, not a valid SQL query
            if question.lower().startswith("how many users"):
                sql_part = "SELECT COUNT(*) FROM users;"
            elif "count" in question.lower() and "users" in question.lower():
                sql_part = "SELECT COUNT(*) FROM users;"
            else:
                sql_part = ""
                debug_info["error"] = "Generated SQL appears to be schema text, not a valid query"
    except Exception as e:
        sql_part = ""
        debug_info["error"] = f"SQL extraction error: {str(e)}"
    
    # Add performance metrics to debug info
    inference_time = time.time() - start_time
    debug_info["inference_time"] = f"{inference_time:.2f}s"
    debug_info["prompt_tokens"] = len(inputs.input_ids[0])
    debug_info["generated_tokens"] = len(outputs[0]) - len(inputs.input_ids[0])
    
    return sql_part, debug_info

def get_db_schema():
    """Fetch schema with caching."""
    CACHE_FILE = "schema_cache.json"
    MAX_CACHE_AGE = 3600  # 1 hour
    
    def fetch_fresh_schema():
        """Actual schema fetching implementation (renamed from original get_db_schema)"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Improved query to get schema information without duplicates
            cursor.execute("""
                SELECT 
                    table_name,
                    STRING_AGG(DISTINCT column_name || ' ' || 
                    CASE WHEN data_type = 'USER-DEFINED' THEN udt_name
                        ELSE data_type END, ', ') AS columns
                FROM information_schema.columns c
                WHERE table_schema = 'public'
                GROUP BY table_name
                ORDER BY table_name
            """)
            
            tables_result = cursor.fetchall()
            
            # Separate query for foreign keys to avoid duplication
            cursor.execute("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    tc.constraint_name
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
                ORDER BY tc.table_name, tc.constraint_name
            """)
            
            fk_result = cursor.fetchall()
            
            schema_parts = []
            schema_json = {"tables": [], "foreign_keys": []}
            
            # Process tables
            for table, columns in tables_result:
                table_def = f"{table}({columns})"
                schema_parts.append(table_def)
                
                # Add to JSON structure
                schema_json["tables"].append({
                    "name": table,
                    "columns": columns
                })
            
            # Process foreign keys (without duplicates)
            processed_fks = set()
            for table, column, ftable, fcolumn, constraint in fk_result:
                fk_text = f"FK: {constraint} → {ftable}({fcolumn})"
                if fk_text not in processed_fks:
                    schema_parts.append(fk_text)
                    schema_json["foreign_keys"].append(fk_text)
                    processed_fks.add(fk_text)
            
            cursor.close()
            conn.close()
            
            # Return both formats
            return {
                "text": '\n'.join(schema_parts),
                "json": schema_json
            }
            
        except Exception as e:
            print(f"🚨 Database connection error: {e}")
            return None

    try:
        # Use cached schema if recent
        if os.path.exists(CACHE_FILE):
            stat = os.stat(CACHE_FILE)
            if (time.time() - stat.st_mtime) < MAX_CACHE_AGE:
                with open(CACHE_FILE, 'r') as f:
                    try:
                        # Try to load as JSON
                        schema_data = json.load(f)
                        if isinstance(schema_data, dict) and "text" in schema_data:
                            return schema_data["text"]
                        else:
                            # If old format, just return the content
                            f.seek(0)
                            return f.read()
                    except json.JSONDecodeError:
                        # If not valid JSON, treat as plain text
                        f.seek(0)
                        return f.read()
                    
        # Fetch fresh schema and cache
        schema_data = fetch_fresh_schema()
        if schema_data:
            with open(CACHE_FILE, 'w') as f:
                json.dump(schema_data, f, indent=2)
            return schema_data["text"]
        return None
    except Exception as e:
        print(f"Schema cache error: {e}")
        schema_data = fetch_fresh_schema()
        return schema_data["text"] if schema_data else None

def main():
    try:
        # Display app header
        print("\n" + "=" * 60)
        print("T2S - Text2SQL Assistant for Event Management")
        print("=" * 60)
        
        # Load model and check database
        model, tokenizer = load_model()
        
        schema = get_db_schema()
        if not schema:
            print("❌ Could not retrieve schema from the database. Exiting...")
            return
        
        optimized_schema = optimize_schema(schema)
        print(f"Schema loaded: {len(schema)} chars → {len(optimized_schema)} chars optimized")
        
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        print(f"Connected to database: {DB_CONFIG['database']}")
        
        # Prepare log directory
        SUCCESS_LOG = os.getenv("LOG_FILE", "text2sql/successful_queries.log")
        os.makedirs(os.path.dirname(SUCCESS_LOG), exist_ok=True)
        
        # Predefined common queries
        common_queries = {
            "list users": "SELECT * FROM users LIMIT 10;",
            "list events": "SELECT * FROM events LIMIT 10;",
            "list venues": "SELECT * FROM venues LIMIT 10;",
            "show tickets": "SELECT * FROM tickets LIMIT 10;",
            "show registrations": "SELECT * FROM registrations LIMIT 10;",
            "event categories": "SELECT * FROM event_categories LIMIT 10;",
            "upcoming events": (
                "SELECT title, description, start_time, end_time, venues.name as venue_name "
                "FROM events JOIN venues ON events.venue_id = venues.venue_id "
                "WHERE start_time > NOW() ORDER BY start_time LIMIT 10;"
            ),
            "popular events": (
                "SELECT events.title, COUNT(registrations.registration_id) as registration_count "
                "FROM events JOIN registrations ON events.event_id = registrations.event_id "
                "GROUP BY events.event_id, events.title ORDER BY registration_count DESC LIMIT 10;"
            )
        }
        
        print("\n Ask a question or type 'exit' to quit\n")
        
        while True:
            try:
                print("\n" + "-" * 60)
                question = input("Ask anything about the event management data: ").strip()
                if question.lower() == "exit":
                    break
                
                sql = None
                debug_info = {}
                
                # Check for common queries first
                for key, query in common_queries.items():
                    if key in question.lower():
                        sql = query
                        debug_info = {
                            "cached_query": True,
                            "inference_time": "0.00s",
                            "model": "cached_response",
                            "device": "n/a",
                            "is_gpu": "n/a"
                        }
                        break
                
                # Generate SQL using the model
                if not sql:
                    with Spinner():
                        sql, debug_info = generate_sql(model, tokenizer, question, optimized_schema)
                
                if sql:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(sql)
                        
                        # Display query information
                        print("\nQuery Result:")
                        print(f"• Input: {question}")
                        print(f"• SQL: {sql}")
                        
                        # Display debug information in a nice format
                        print("\nPerformance Info:")
                        for key, value in debug_info.items():
                            print(f"  • {key}: {value}")
                        
                        # Try to fetch results
                        if cursor.description:  # Has results to fetch
                            results = cursor.fetchall()
                            colnames = [desc[0] for desc in cursor.description]
                            
                            if not results:
                                print("\nNo results returned (query executed successfully)")
                            else:
                                print(f"\nResults ({len(results)} rows):")
                                print("-" * 60)
                                print(" | ".join(colnames))
                                print("-" * 60)
                                
                                # Show at most 15 rows to avoid flooding the console
                                for row in results[:15]:
                                    print(" | ".join(str(cell) for cell in row))
                                
                                if len(results) > 15:
                                    print(f"... and {len(results) - 15} more rows")
                        else:
                            # For non-SELECT queries
                            print(f"\nQuery executed successfully (no results to fetch)")
                            
                        # Log the successful query
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "question": question,
                            "sql": sql,
                            "debug_info": debug_info
                        }
                        with open(SUCCESS_LOG, "a") as f:
                            f.write(json.dumps(log_entry) + "\n")
                            
                    except Exception as e:
                        print(f"\n🚨 SQL Execution Error: {e}")
                        print(f"Generated SQL was: {sql}")
                    finally:
                        cursor.close()
                else:
                    print("\n❌ Failed to generate SQL query")
                
            except KeyboardInterrupt:
                print("\n⚠️ Operation cancelled by user")
                break
            except Exception as e:
                print(f"\n🚨 Error: {e}")
        
        conn.close()
        print("\n👋 Thank you for using T2S !")
    
    except Exception as e:
        print(f"\n🚨 Critical error: {e}")

if __name__ == "__main__":
    main()