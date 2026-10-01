# Text-to-SQl-Rag-System

A multi-agent Text-to-SQl system that allows users to ask question about postgresql database using natural language.
the system understands the user's query , genrates a SQL query , executes it on database and returns the result as natural language answer.
It aslo has role-based access control for admin,analyst and viewer for users.

## Features

- Ask questions about PostgreSQL data using natural language
- Generate SQL queries automatically from user questions
- Return query results along with a natural-language answer
- Multi-agent workflow using LangGraph
- Role-based access control with Admin, Analyst, and Viewer roles
- Authentication using Bearer tokens
- Reject unsafe or write-enabled SQL queries
- Handle invalid queries and cases where no matching records are found
- Streamlit web interface
- FastAPI backend

## Tech Stack

- Python
- FastAPI
- LangChain
- LangGraph
- Groq LLM
- PostgreSQL
- Psycopg2
- Streamlit
- Pydantic
- Uvicorn

## Project Structure

```text
Text-to-SQl-Rag-System/
│
├── database/
│   ├── Schema.sql
│   └── seed.py
├── frontend/
|   ├── streamlit.py
|
├── src/
│   └── text_to_sql_rag_system/
│
|
├── app.py
├── backend.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── uv.lock
```

# Installation

1.Clone the repository and move into the project directory:

    git clone https://github.com/riteshsal/Text-to-SQl-Rag-System.git
    cd Text-to-SQl-Rag-System

2.Create and activate a virtual environment:

    python -m venv .venv

On Windows:

    .venv\Scripts\activate

On Linux/macOS:

    source .venv/bin/activate

3.Install the required dependencies:

    pip install -r requirements.txt

4.Create a `.env` file in the project root and add:

    DATABASE_URL=your_postgresql_connection_string
    GROQ_API_KEY=your_groq_api_key

5.Set up the database using `database/Schema.sql` and then run the run_schema.py to create schema then run seed script to insert fake data:

    python database/seed.py

6.Start the FastAPI backend:

    uvicorn app:app --reload

7.Open another terminal and start the Streamlit frontend:

    streamlit run streamlit.py


## Architecture

The system uses a multi-agent workflow built with LangGraph.

This workflow has four agents:

1. **Query Understanding Agent**
   - Understands the user's natural language question.
   - Identifies the intent, tables, columns, filters, aggregations, grouping, ordering, limits, and date ranges.

2. **SQL Generation Agent**
   - Uses the query understanding and database schema to generate a PostgreSQL SQL query.
   - Generates only read-only SQL queries.

3. **SQL Execution Agent**
   - Validates the generated SQL query.
   - Executes the query on PostgreSQL.
   - Returns the columns, rows, and row count.
   - Handles cases where no matching records are found.

4. **Answer Synthesis Agent**
   - Uses the SQL result to generate a natural-language answer.
   - Does not add information that is not present in the query result.

The overall workflow is:

    User Question
          ↓
    Query Understanding Agent
          ↓
    SQL Generation Agent
          ↓
    SQL Execution Agent
          ↓
    Answer Synthesis Agent
          ↓
    Final Answer


## API Usage

The application provides a Streamlit web interface for interacting with the Text-to-SQL system.

### Available Tokens

| Token | Role |
|---|---|
| `admin-token` | Admin |
| `analyst-token` | Analyst |
| `viewer-token` | Viewer |

### Using the Streamlit Application

1. Start the FastAPI backend.
2. Start the Streamlit application.
3. Enter one of the available tokens in the **Authentication Token** field.
4. Enter your question in the **Ask your question** field.
5. Click **Ask**.

For example:

    Authentication Token: analyst-token

    Question: How many customers are there?

The application sends the question and token to the FastAPI backend.

### Response

For **Admin** and **Analyst** users, the application displays:

- Final answer
- Generated SQL
- Database schema
- Query result

For **Viewer** users, only the final answer is displayed.

### Example

Question:

    How many customers are there?

The application may return:

    Answer:
    There are 200 customers.

    Generated SQL:
    SELECT COUNT(*) FROM customers;

    Result:
    columns: ["count"]
    rows: [[200]]
    row_count: 1


## Role-Based Access Control and permission matrix

The application has three roles:

| Role | Access |
|---|---|
| Admin | Answer, SQL, schema, and result |
| Analyst | Answer, SQL, schema, and result |
| Viewer | Final answer only |

Authentication and role checking are handled by FastAPI middleware.

The API returns:

- `401` is returned when authentication is missing or the token is invalid.
- All three defined roles are allowed to access `/ask`.


## Error Handling and Security

The application handles common errors during the Text-to-SQL workflow.

- Missing or invalid authentication token returns `401`.
- Questions that are outside the database scope are rejected.
- Unsafe or write-enabled SQL queries are rejected.
- Database errors are handled without allowing write operations.
- If a query returns no matching records, the application returns a clear no-records message.
- Invalid table or column requests are handled by the application.


## Authentication/Authorization middleware flow
User
  ↓
Streamlit UI
  ↓
Bearer Token
  ↓
FastAPI Middleware
  ↓
Check token
  ├── Missing/Invalid → 401
  │
  └── Valid
        ↓
     Identify Role
        ↓
   Check request/question
        ↓
   /ask endpoint
        ↓
   LangGraph workflow
        ↓
   Response based on role
        ├── Admin   → Answer + SQL + Schema + Result
        ├── Analyst → Answer + SQL + Schema + Result
        └── Viewer  → Answer only



## Example Queries

The following are some example questions that can be tested using the application.

### Direct Lookup
    How many customers are there?
    How many products are there?

### Filtering
    Show all customers from Calderonton city.
    Show products with a unit_price greater than 400

### Aggregation
    What is the total number of orders?
    What is the average product unit_price?

### Joins
    Show the names of first 10 customers and their orders items name.

    Show the total amount spent by each customer.

### Grouping
    How many orders has each customer placed?

### Date / Temporal Queries
    How many orders were placed in 2025?
    How many orders were placed in 2024 each quarter?

### No Result / Invalid Queries

    Show customers from a city that does not exist.

    What is the average salary of customers?

### Out-of-Scope Questions

    What is the weather today?

    Who is the Prime Minister of India?


## Future Improvements

- Replace the current hardcoded authentication tokens with JWT-based authentication.
- Implement role-based authorization using JWT roles for Admin, Analyst, and Viewer.
- Alternatively, integrate OAuth 2.0 / OpenID Connect for user authentication and authorization.
- Add user registration and login instead of using predefined tokens.
- Add more advanced query validation and SQL security checks.
- Improve the UI with better result tables and query history.
