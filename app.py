from fastapi import FastAPI, HTTPException, Request ,Security
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.security import HTTPBearer
from backend import (
    graph,
    build_initial_state,
    UnsafeSQLError,
    SQLGenerationError,
    QueryUnderstandingError,
    DatabaseError,
    AnswerGenerationError,
)
import re

app = FastAPI()
security=HTTPBearer() #defines a Bearer authentication scheme.

# Temporary users for testing
USERS = {
    "admin-token": "Admin",
    "analyst-token": "Analyst",
    "viewer-token": "Viewer"
}


# Authentication Middleware

@app.middleware("http")
async def auth_middleware(request: Request, call_next):

    # Protect only the /ask endpoint
    if request.url.path == "/ask":

        authorization = request.headers.get("Authorization")

        # No authentication provided
        if not authorization:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Authentication required"
                }
            )

        # Check Bearer format
        if not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid authentication format"
                }
            )

        # Extract token
        token = authorization.replace("Bearer ", "", 1)

        # Find user's role
        role = USERS.get(token)

        # Invalid token
        if role is None:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid authentication token"
                }
            )

        # Store authenticated user's role
        request.state.role = role

         # Unsafe / write request check
        if request.method == "POST":

            body = await request.json()
            question = body.get("question", "")

            forbidden_words = [
                "delete",
                "drop",
                "update",
                "insert",
                "truncate",
                "alter",
                "create"
            ]

            question_lower = question.lower()

            if any(word in question_lower for word in forbidden_words):
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Unsafe or write-enabled SQL query is not allowed."
                    }
                )

    response = await call_next(request)

    return response



# Request Model

class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(
    request: AskRequest,
    http_request: Request,
    credentials=Security(security)
):

    
    role = http_request.state.role

    try:
        result = graph.invoke(
            build_initial_state(request.question)
        )

        if role == "Viewer":
            return {
                "answer": result["answer"]
            }


        if role in ["Admin", "Analyst"]:
            return {
                "answer": result["answer"],
                "schema": result["schema"],
                "sql": result["sql"],
                "result": result["result"]
            }

        # ------------------------------------------
        # Unknown / insufficient role
        # ------------------------------------------

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    except HTTPException:
        raise

    except HTTPException:
        raise

    except UnsafeSQLError as e:
            # The generated SQL itself was rejected - a bad/unsafe request
        raise HTTPException(status_code=400, detail=str(e))

    except (QueryUnderstandingError, SQLGenerationError) as e:
            # The AI couldn't turn the question into a valid query.
        raise HTTPException(status_code=422, detail=str(e))

    except DatabaseError as e:
            # The query was valid and safe, but actually failed to run.
        raise HTTPException(status_code=500, detail=str(e))

    except AnswerGenerationError as e:
            # SQL succeeded, but the final LLM write-up failed.
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
            # True catch-all for anything genuinely unexpected.
        raise HTTPException(status_code=500, detail=str(e))