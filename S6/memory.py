import sqlite3
from models import GetSTMemoryInput, GetSTMemoryOutput, UpdateSTMemoryInput
from logger import get_logger

#Get the instance of logger
logger = get_logger()

# --- SHORT TERM MEMORY ---
short_term_memory = {}

def get_short_term_memory(input:GetSTMemoryInput) -> GetSTMemoryOutput:
    
    if input.key not in short_term_memory:
        logger.debug(f"No memory found for the key: {input.key}")
        return ""
    else:
        memory_list = short_term_memory.get(input.key, [])
        logger.debug(f"Retrieved {len(memory_list)} memory items for key: {input.key}")
        return " ".join(str(item) for item in memory_list)
    
def get_last_response(input:GetSTMemoryInput) -> GetSTMemoryOutput:
    
    if input.key not in short_term_memory:
        logger.debug(f"No memory found for key: {input.key}")
        return ""
    else:
        memory_list = short_term_memory.get(input.key, [])
        if len(memory_list) > 0:
            logger.debug(f"Retrieved last response for key: {input.key}")
            return str(memory_list[-1])
        logger.debug(f"Memory list empty for key: {input.key}")
        return ""

def update_short_term_memory(input:UpdateSTMemoryInput):
   
    if input.key not in short_term_memory:
        logger.debug(f"Creating new memory entry for key: {input.key}")
        short_term_memory[input.key] = []
    short_term_memory[input.key].append(input.value)
    logger.info(f"Memory Updated for key: {input.key}, current size: {len(short_term_memory[input.key])}")

def reset_short_term_memory():
    global short_term_memory
    logger.info("Resetting all short-term memory")
    short_term_memory = {}



# --- LONG TERM MEMORY ---

# # Initialize SQLite3 database and table
# def _init_long_term_memory_db():
#     conn = sqlite3.connect("long_term_memory.db")
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS memory (
#             key TEXT PRIMARY KEY,
#             value TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()

# # Only initialize if DB file does not exist
# if not os.path.exists("long_term_memory.db"):
#     _init_long_term_memory_db()

# def get_long_term_memory(key):
#     """Fetches the value associated with the key from long-term memory."""
#     conn = sqlite3.connect("long_term_memory.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT value FROM memory WHERE key = ?", (key,))
#     row = cursor.fetchone()
#     conn.close()
#     return row[0] if row else None

# def update_long_term_memory(key, value):
#     """Inserts or updates a key-value pair in the long-term memory database."""
#     conn = sqlite3.connect("long_term_memory.db")
#     cursor = conn.cursor()
#     cursor.execute("""
#         INSERT INTO memory (key, value)
#         VALUES (?, ?)
#         ON CONFLICT(key) DO UPDATE SET value = excluded.value
#     """, (key, value))
#     conn.commit()
#     conn.close()
