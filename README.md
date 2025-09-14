Automated Fintech Data & AI Insights Pipeline
This project is an automated, cloud-hosted pipeline that fetches daily financial data, stores it in a PostgreSQL database, and uses an AI to generate actionable insights and recommendations.
The entire process is deployed and scheduled to run automatically on Railway.app.

📊 Project Overview
The pipeline automates the following daily tasks:
Data Fetching: Pulls daily stock performance data for a specified symbol from the Alpha Vantage API.
Data Storage: Inserts the fetched data into a normalized PostgreSQL database, providing a historical record.
AI Analysis: Sends the most recent day's data to a Large Language Model (LLM) via the OpenAI API, prompting it to act as a fintech analyst.
Insight Storage: Saves the LLM's summary and recommendations back into the database for review.
This system is perfect for tracking financial or business performance metrics and getting daily, intelligent analysis without any manual intervention.

🚀 Key Technologies
Backend: Python
Data Fetching: Alpha Vantage API
AI Integration: OpenAI API
Database: PostgreSQL
Cloud Platform: Railway.app (for hosting and scheduling)

📁 Repository Structure
main.py: The core Python script that orchestrates the entire pipeline (fetch, store, analyze).
migrate.py: A utility script to set up the PostgreSQL database schema.
requirements.txt: Lists all Python dependencies required by the project.
Procfile: A special file that tells Railway how to run the application as a scheduled cron job.

schema.sql: The SQL script used to create the database tables.
.gitignore: Tells Git to ignore unnecessary files and folders, like the virtual environment (venv).

⚙️ Setup and Deployment Guide
Follow these steps to deploy your own instance of this pipeline on Railway.
Step 1: Set Up Railway Services
Create a new project on Railway.app.
Add a PostgreSQL database service.
Add an Empty Service for your Python application.
In the Variables tab of your empty service, add the following environment variables:
ALPHA_VANTAGE_API_KEY: Your API key.
OPENAI_API_KEY: Your OpenAI API key.
DATABASE_URL: Copy this from the Connect tab of your PostgreSQL service.

Step 2: Push Code to GitHub
Clone this repository to your local machine.
Add your files (main.py, migrate.py, etc.).
Initialize a Git repository and commit your files.
Create a new, empty repository on GitHub and push your local code to it.
Note: The .gitignore file ensures that your virtual environment (venv/) is not committed to your repository.

Step 3: Connect and Deploy on Railway
In your Railway project, navigate to the Empty Service.
Click the "Make a deployment to get started →" button.
Choose to "Deploy from GitHub Repo" and authorize Railway to access your repository.
Select the correct repository from the list. Railway will automatically build and deploy your project.

Step 4: Run Database Migrations
Before the pipeline can run, you must create the database tables.
Navigate to the Deployments tab in your application service.
Look for a section to run a manual command.
Enter the command: python migrate.py
Click Run to execute the script and create your database schema. You only need to do this once.

Step 5: Schedule the Daily Job
Navigate to the Settings tab of your application service.
On the left, select Plugins and add the Cron plugin.
Set the Cron expression to 0 0 * * * (to run every day at midnight).
Set the Command to python main.py.

⚙️ How to Customize
Change the Stock Symbol: In main.py, change the STOCK_SYMBOL variable to any symbol supported by Alpha Vantage (e.g., GOOG, TSLA).
Use a Different API: To use a different data source (e.g., Clearbit, Plaid), you would need to:
Update the fetch_daily_stock_data function in main.py to make the correct API call.
Modify the schema.sql file to match the new data structure.

