# T2S - Text2SQL (context: Event Management) 

*Because who has time to write SQL queries when you can just ask in plain English?* 😉

Welcome to **Text2SQL for Event Management**, your AI-powered assistant for querying event data without writing a single line of SQL. This application transforms your natural language questions into powerful SQL queries, making database interactions a breeze!


## 🌟 Features

- **Natural Language to SQL:** Say goodbye to complex SQL syntax! Just ask questions in plain English and watch the magic happen.
  
- **Optimized for Event Management:** Specifically designed for event management databases with tables for users, events, venues, tickets, and more.
  
- **Apple Silicon Optimized:** Blazing fast performance on Apple Silicon (M1/M2/M3) with MPS acceleration.
  
- **Interactive Experience:** Clean, user-friendly interface that makes database querying accessible to everyone, regardless of technical background.
  
- **Comprehensive Schema Support:** Full understanding of relationships between users, events, venues, tickets, registrations, and more.

## 📊 Database Schema

Our event management database contains these interconnected tables:

- **users:** User information (attendees, organizers, admins)
- **venues:** Event venue information with location details
- **events:** Comprehensive event details including time and location
- **tickets:** Ticket information for events with pricing tiers
- **registrations:** User registrations for events
- **event_categories:** Categories for organizing events
- **event_category_mapping:** Mapping between events and categories
- **payments:** Payment information for registrations
- **notifications:** Notifications sent to users

## 🚀 Quick Setup

Want to get started in seconds? Just run our setup script:

```bash
# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This script will:
1. Check for prerequisites (Python, Docker)
2. Create a virtual environment
3. Install all dependencies
4. Set up your environment variables
5. Start the PostgreSQL database
6. Generate sample data
7. Get everything ready for you to start querying!

## 🛠️ Manual Setup

Prefer to do things step by step? No problem!

1. **Install Dependencies:**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

2. **Configure Environment:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit with your database details
```

3. **Start the Database:**
```bash
# Launch PostgreSQL with Docker
docker-compose up -d
```

4. **Generate Sample Data:**
```bash
# Create and populate database tables
python data.py
```

5. **Run the Application:**
```bash
# Start the Text2SQL application
python main.py
```

## 🔮 Environment Variables

The application uses these environment variables:

**Required:**
- `DB_HOST`: Database host address
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

**Optional:**
- `CACHE_DIR`: Custom directory for model cache (default: ./model_cache)
- `LOG_FILE`: Custom path for query logs (default: ./text2sql/successful_queries.log)

## 💬 Example Queries

Once the application is running, try asking these questions:

- "List all events happening in Dallas" 🏙️
- "Show me the top 5 events with the most registrations" 🏆
- "How many tickets have been sold for the Dallas Tech Conference?" 🎟️
- "What is the total revenue from all events?" 💰
- "Which venues have the highest capacity?" 🏟️
- "List all users who registered for more than 3 events" 👥

The application will convert your question into SQL and execute it against the database, displaying the results in a clean format.

## 🧠 How It Works

Peek under the hood at the magic behind Text2SQL:

1. **Natural Language Processing:**
   - Utilizes a fine-tuned language model to understand the intent of your questions.
   - Analyzes the semantic meaning and context to generate appropriate SQL queries.

2. **Database Schema Understanding:**
   - Automatically extracts and optimizes the database schema.
   - Understands relationships between tables for accurate query generation.

3. **Query Execution:**
   - Safely executes the generated SQL against your PostgreSQL database.
   - Returns formatted results for easy reading and analysis.

4. **Performance Optimization:**
   - Leverages Apple Silicon GPU acceleration when available.
   - Implements efficient tokenization and model loading for quick responses.

## 🤝 Contributing

Got ideas to make this even better? Contributions are welcome!

1. **Fork the Repository**
2. **Create a Feature Branch** (`git checkout -b feature/YourFeature`)
3. **Commit Your Changes** (`git commit -m 'Add some feature'`)
4. **Push to the Branch** (`git push origin feature/YourFeature`)
5. **Open a Pull Request**


---

*Happy querying! May your data always be just a question away.* ✨

