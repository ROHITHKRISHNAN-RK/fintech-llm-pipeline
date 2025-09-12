import os
import requests
import psycopg2
from datetime import date, timedelta
from dotenv import load_dotenv
import openai

# --- Step 1: Load Environment Variables ---
# This line loads the secret keys from the .env file for local testing.
# Railway handles these automatically, so you don't need a .env file there.
load_dotenv()

# --- Step 2: Configuration ---
# We get our secret keys from the environment variables we set in Railway.
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
STOCK_SYMBOL = "IBM" # You can change this to any stock symbol you want to track.

# Initialize the OpenAI client with your API key
openai.api_key = OPENAI_API_KEY

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def fetch_daily_stock_data(symbol, api_key):
    """
    Fetches daily adjusted stock data from the Alpha Vantage API.
    
    This function makes a web request to the API and gets back data about a stock.
    """
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        
        # Check for API-specific error messages
        if "Error Message" in data:
            print(f"API Error: {data['Error Message']}")
            return None
        
        return data.get("Time Series (Daily)", None)
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during data fetching: {e}")
        return None

def store_daily_data(conn, symbol, daily_data):
    """
    Stores the most recent day's data into the daily_stock_data table.
    
    This function takes the data from the API and saves it into your database.
    It uses a special command to avoid errors if the data for the day already exists.
    """
    if not daily_data:
        print("No daily data to store.")
        return False

    # Get the latest date from the data
    latest_date_str = sorted(daily_data.keys())[-1]
    latest_date_data = daily_data[latest_date_str]
    
    try:
        data_tuple = (
            latest_date_str,
            symbol,
            float(latest_date_data['1. open']),
            float(latest_date_data['2. high']),
            float(latest_date_data['3. low']),
            float(latest_date_data['4. close']),
            float(latest_date_data['5. adjusted close']),
            int(latest_date_data['6. volume']),
            float(latest_date_data['7. dividend amount']),
            float(latest_date_data['8. split coefficient'])
        )

        cursor = conn.cursor()
        query = """
        INSERT INTO daily_stock_data (
            date, symbol, open, high, low, close, adjusted_close, 
            volume, dividend_amount, split_coefficient
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            adjusted_close = EXCLUDED.adjusted_close,
            volume = EXCLUDED.volume,
            dividend_amount = EXCLUDED.dividend_amount,
            split_coefficient = EXCLUDED.split_coefficient,
            last_updated = NOW();
        """
        cursor.execute(query, data_tuple)
        conn.commit() # Save the changes to the database
        cursor.close()
        print(f"Successfully stored data for {latest_date_str}")
        return True
    except (psycopg2.Error, Exception) as e:
        conn.rollback() # Undo changes if there's an error
        print(f"Error storing data: {e}")
        return False

def get_latest_data_from_db(conn):
    """
    Retrieves the most recent day's data from the database.
    
    This is so we can send only the latest data to the AI for analysis.
    """
    try:
        cursor = conn.cursor()
        query = """
        SELECT date, open, high, low, close, adjusted_close, volume
        FROM daily_stock_data
        ORDER BY date DESC
        LIMIT 1;
        """
        cursor.execute(query)
        latest_row = cursor.fetchone()
        cursor.close()
        return latest_row
    except (psycopg2.Error, Exception) as e:
        print(f"Error retrieving latest data: {e}")
        return None

def get_llm_insights(data):
    """
    Sends the latest data to an LLM for analysis and recommendations.
    
    This function talks to the OpenAI API and gets back the summary and advice.
    """
    if not data:
        print("No data to send to LLM.")
        return None
        
    date_str, open_price, high, low, close, adjusted_close, volume = data

    prompt = f"""
    You are a fintech analyst. Based on the following performance data for {date_str} for a single stock, provide a short summary and 3 actionable recommendations to improve performance for this stock's investors. 
    
    The data represents the daily performance of a stock:
    - Open Price: ${open_price:.2f}
    - High Price: ${high:.2f}
    - Low Price: ${low:.2f}
    - Close Price: ${close:.2f}
    - Adjusted Close Price: ${adjusted_close:.2f}
    - Volume: {volume:,}

    Please provide your response in the following format:
    Summary: [Your short summary here]
    Recommendation 1: [First actionable recommendation]
    Recommendation 2: [Second actionable recommendation]
    Recommendation 3: [Third actionable recommendation]
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",  # You can also use "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful fintech analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        llm_response_text = response.choices[0].message.content
        print("LLM Response:\n", llm_response_text)
        
        # Parse the AI's response to get the summary and recommendations
        summary = ""
        recs = ["", "", ""]
        lines = llm_response_text.split('\n')
        for line in lines:
            if line.startswith("Summary:"):
                summary = line.replace("Summary:", "").strip()
            elif "Recommendation 1:" in line:
                recs[0] = line.replace("Recommendation 1:", "").strip()
            elif "Recommendation 2:" in line:
                recs[1] = line.replace("Recommendation 2:", "").strip()
            elif "Recommendation 3:" in line:
                recs[2] = line.replace("Recommendation 3:", "").strip()
        
        return summary, recs
        
    except Exception as e:
        print(f"Error getting LLM insights: {e}")
        return None, None

def store_llm_recommendations(conn, analysis_date, summary, recs):
    """
    Stores the LLM's insights and recommendations into the database.
    """
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO daily_recommendations (
            analysis_date, llm_summary, recommendation_1, 
            recommendation_2, recommendation_3
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (analysis_date) DO UPDATE SET
            llm_summary = EXCLUDED.llm_summary,
            recommendation_1 = EXCLUDED.recommendation_1,
            recommendation_2 = EXCLUDED.recommendation_2,
            recommendation_3 = EXCLUDED.recommendation_3,
            created_at = NOW();
        """
        cursor.execute(query, (analysis_date, summary, recs[0], recs[1], recs[2]))
        conn.commit()
        cursor.close()
        print(f"Successfully stored LLM recommendations for {analysis_date}")
        return True
    except (psycopg2.Error, Exception) as e:
        conn.rollback()
        print(f"Error storing LLM recommendations: {e}")
        return False

def main():
    """Main function to run the entire data pipeline."""
    print("Starting the daily ETL and LLM analysis pipeline...")

    # Step 1: Fetch data from the API
    daily_data = fetch_daily_stock_data(STOCK_SYMBOL, ALPHA_VANTAGE_API_KEY)
    if not daily_data:
        print("Pipeline aborted due to data fetching error.")
        return

    # Step 2: Store data in the database
    conn = get_db_connection()
    if not conn:
        print("Pipeline aborted due to database connection error.")
        return

    store_daily_data(conn, STOCK_SYMBOL, daily_data)

    # Step 3: Get the latest data from the database for LLM analysis
    latest_data = get_latest_data_from_db(conn)
    if not latest_data:
        print("Pipeline aborted as no data was found in the database.")
        conn.close()
        return

    analysis_date = latest_data[0] # Get the date from the fetched tuple
    
    # Step 4: Get insights from the LLM
    llm_summary, llm_recs = get_llm_insights(latest_data)
    if not llm_summary:
        print("Pipeline aborted due to LLM analysis error.")
        conn.close()
        return

    # Step 5: Store the LLM's recommendations
    store_llm_recommendations(conn, analysis_date, llm_summary, llm_recs)
    
    conn.close()
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
