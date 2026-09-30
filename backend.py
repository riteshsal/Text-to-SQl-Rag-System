import os 
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph,START,END
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import re
from typing import TypedDict,Any

DATABASE_URL=os.getenv("DATABASE_URL")
GROQ_API_KEY=os.getenv("GROQ_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

#llm
llm=ChatGroq(
    model="openai/gpt-oss-120b"
    )

#database connection
def get_db():
    """create a postgresql database connection """
    return psycopg2.connect(DATABASE_URL)

#shared state
class SQLState(TypedDict):
    question:str
    understanding:str
    schema:str
    sql:str
    result:str
    answer:str

#creating custom exceptions to handle errors in each agent
class SQLGenerationError(Exception):
    pass


class UnsafeSQLError(Exception):
    pass


class DatabaseError(Exception):
    pass


class NoRecordsFound(Exception):
    pass



#query understanding agent
def clean_json_response(content: str):
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    return json.loads(content)

def query_understanding_agent(state:SQLState):
    question=state['question']
    prompt=ChatPromptTemplate.from_template(
        """
        You are a Query Understanding Agent for a Text-to-SQL system.

        Analyze the user's natural language question and identify:

        1. intent
        2. relevant tables
        3. relevant columns
        4. filters
        5. aggregation
        6. group_by
        7. order_by
        8. limit
        9. date_range

        Return ONLY valid JSON.

        User question:
        {question}
        """
    )

    chain=prompt|llm
    response=chain.invoke({"question":question})
    understanding=clean_json_response(response.content)

    return {
        "understanding":understanding
    }

#sql generation agent
def clean_sql_response(content: str):
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```sql", "").replace("```", "").strip()

    return content


def sql_generation_agent(state:SQLState):
    try:
        question=state['question']
        understanding=state['understanding']
        schema=state['schema']

        prompt = ChatPromptTemplate.from_template("""
        You are a SQL Generation Agent.

        Generate a PostgreSQL SQL query based on:

        User question:
        {question}

        Query understanding:
        {understanding}

        Database schema:
        {schema}

        Rules:
        - Generate only SELECT queries.
        - Use only tables and columns from the provided schema.
        - Do not invent table or column names.
        - Use valid PostgreSQL syntax.
        - Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
        - Return only the SQL query, without explanation or markdown.
        """)

        chain = prompt | llm

        response = chain.invoke({
            "question": question,
            "understanding": understanding,
            "schema": schema
        })

        sql=clean_sql_response(response.content)

        if not sql:
            raise SQLGenerationError("SQL query could not be generated")

        return {
            "sql":sql
        }
    except Exception as e:
        raise SQLGenerationError(f"Failed to generate SQl query ;{str(e)}")


#sql execution agent
import re

def validate_sql(sql: str):
    sql = sql.strip()

    # Only SELECT or WITH queries are allowed
    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")

    # Block write/destructive operations
    forbidden = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|MERGE)\b"

    if re.search(forbidden, sql, re.IGNORECASE):
        raise ValueError("Unsafe SQL query detected.")

    # Prevent multiple SQL statements
    if ";" in sql.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed.")

    return sql


def sql_execution_agent(state: SQLState):
    sql = state["sql"]

    try:
        validate_sql(sql)

        connection = get_db()
        cursor = connection.cursor()

        cursor.execute(sql)

        rows = cursor.fetchall()

        if not rows:
            return {
                "result": {
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "message": "No matching records found."
                }
            }

        columns = [desc[0] for desc in cursor.description]

        return {
            "result": {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
        }

    except ValueError as e:
        raise UnsafeSQLError(str(e))

    except Exception as e:
        raise DatabaseError(
            f"The requested information is not available in the database."
        )

    finally:
        if "cursor" in locals():
            cursor.close()

        if "connection" in locals():
            connection.close()


#answer agent
def answer_agent(state:SQLState):
    try:
        question=state['question']
        result=state['result']

        prompt = ChatPromptTemplate.from_template("""
        You are an Answer Synthesis Agent.

        Answer the user's question using only the SQL result provided.

        User question:
        {question}

        SQL result:
        {result}

        Rules:
        - Give a clear, concise natural-language answer.
        - Do not invent information.
        - If there are no rows, clearly say that no matching records were found.
        """)

        chain = prompt | llm

        response = chain.invoke({
            "question": question,
            "result": result
        })

        answer=response.content

        if not answer:
            raise ValueError("Answer could not be generated")
        
        return {
            "answer": answer
        }
    except Exception as e:
        raise Exception(f"Answer failed: {str(e)}")




#getting databaase schema 

with open("database/Schema.sql","r") as f:
    schema= f.read()

def build_initial_state(user_question: str):
    return {
        "question": user_question,
        "schema": schema
    } 


#building graph

graph_builder=StateGraph(SQLState)

graph_builder.add_node("query_understanding",query_understanding_agent)
graph_builder.add_node("sql_generation",sql_generation_agent)
graph_builder.add_node("sql_execution",sql_execution_agent)
graph_builder.add_node("answer",answer_agent)

graph_builder.add_edge(START,"query_understanding")
graph_builder.add_edge("query_understanding","sql_generation")
graph_builder.add_edge("sql_generation", "sql_execution")
graph_builder.add_edge("sql_execution", "answer")
graph_builder.add_edge("answer", END)

graph = graph_builder.compile()

"""result = graph.invoke(
    build_initial_state("Show all employees who work in the Sales department.")
)

print(result["answer"])
"""