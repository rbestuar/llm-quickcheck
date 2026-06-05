"""
Tool Calling Test
-----------------
Tests whether a model correctly uses tools in an agentic coding workflow.

Evaluates three things:
  1. Call/no-call discrimination — does it know WHEN to use a tool?
  2. Tool selection — does it pick the RIGHT tool?
  3. Argument quality — are the args reasonable, not hallucinated?

All tools are sandbox-only. Nothing is ever executed.
Graded by LLM judge.
"""

TEST_ID = "tool_calling"
TEST_NAME = "Tool Calling (Agentic Coding)"
GRADING = "llm_judge"
TEST_DESCRIPTION = "Validates tool call decisions — correct tool selection, argument quality, and knowing when NOT to call a tool"

# ---------------------------------------------------------------------------
# Sandbox tool definitions (OpenAI function-calling format)
# These are sent to the model but never executed.
# ---------------------------------------------------------------------------

SANDBOX_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_file",
            "description": "Read the contents of a file in the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file, e.g. src/auth.py",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run a test file and return pass/fail results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_file": {
                        "type": "string",
                        "description": "Path to the test file, e.g. tests/test_auth.py",
                    }
                },
                "required": ["test_file"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Semantically search the codebase for relevant code or symbols.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of what to find.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_git_log",
            "description": "Retrieve recent git commit history for a branch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "Branch name, e.g. main",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of commits to return.",
                    },
                },
                "required": ["branch"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file in the codebase with specified content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path for the new file.",
                    },
                    "content": {
                        "type": "string",
                        "description": "File content to write.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Test cases
# Each case defines:
#   prompt           - what gets sent to the model
#   should_call      - True if a tool call is expected
#   expected_tool    - which tool should be called (None if should_call=False)
#   expected_args    - key args that must appear (None if should_call=False)
#   correct_behavior - what a good model does
#   bad_behavior     - what a weak model does
# ---------------------------------------------------------------------------

CASES = [
    {
        "id": "run_tests_explicit",
        "prompt": "Run the auth tests and tell me if they pass.",
        "should_call": True,
        "expected_tool": "run_tests",
        "expected_args": {"test_file": "auth"},  # value should contain 'auth'
        "correct_behavior": "Calls run_tests with a path referencing auth tests.",
        "bad_behavior": "Answers without calling any tool, or calls the wrong tool.",
    },
    {
        "id": "get_file_explicit",
        "prompt": "Show me the contents of src/auth.py",
        "should_call": True,
        "expected_tool": "get_file",
        "expected_args": {"path": "src/auth.py"},
        "correct_behavior": "Calls get_file with path='src/auth.py' or very close to it.",
        "bad_behavior": "Makes up the file content without calling the tool, or uses wrong path.",
    },
    {
        "id": "git_log_natural_language",
        "prompt": "What changed on main in the last 5 commits?",
        "should_call": True,
        "expected_tool": "get_git_log",
        "expected_args": {"branch": "main"},
        "correct_behavior": "Calls get_git_log with branch='main' and a reasonable limit.",
        "bad_behavior": "Answers without calling the tool, or hallucinates commit history.",
    },
    {
        "id": "search_codebase_vague",
        "prompt": "Where is the login logic handled in this codebase?",
        "should_call": True,
        "expected_tool": "search_codebase",
        "expected_args": {"query": "login"},  # query should relate to login/auth
        "correct_behavior": "Calls search_codebase with a query related to login or authentication.",
        "bad_behavior": "Guesses a file path without searching, or calls get_file with a hallucinated path.",
    },
    {
        "id": "no_call_explain_concept",
        "prompt": "What's the difference between authentication and authorization?",
        "should_call": False,
        "expected_tool": None,
        "expected_args": None,
        "correct_behavior": "Answers directly from knowledge. No tool call needed or appropriate.",
        "bad_behavior": "Calls search_codebase or any other tool unnecessarily for a general knowledge question.",
    },
    {
        "id": "no_call_explain_code",
        "prompt": "Can you explain what a decorator does in Python?",
        "should_call": False,
        "expected_tool": None,
        "expected_args": None,
        "correct_behavior": "Explains Python decorators from knowledge without calling any tool.",
        "bad_behavior": "Calls search_codebase or get_file to look up decorators unnecessarily.",
    },
    {
        "id": "create_file_with_content",
        "prompt": "Create a new file at utils/helpers.py with a function that reverses a string.",
        "should_call": True,
        "expected_tool": "create_file",
        "expected_args": {"path": "utils/helpers.py"},
        "correct_behavior": "Calls create_file with path='utils/helpers.py' and content containing a string-reversal function.",
        "bad_behavior": "Just shows the code in the chat without calling create_file, or uses the wrong path.",
    },
    {
        "id": "no_call_git_concept",
        "prompt": "What does git rebase do?",
        "should_call": False,
        "expected_tool": None,
        "expected_args": None,
        "correct_behavior": "Explains git rebase from knowledge. No tool call appropriate.",
        "bad_behavior": "Calls get_git_log or any tool to answer a conceptual question.",
    },
]


JUDGE_RUBRIC = """You are a strict evaluator assessing whether an AI model correctly handled a tool-calling decision in an agentic coding assistant context.

Available tools were: get_file, run_tests, search_codebase, get_git_log, create_file.

The prompt sent to the model was:
\"{prompt}\"

Expected behavior:
- Should the model have called a tool? {should_call}
- If yes, expected tool: {expected_tool}
- If yes, expected args hint: {expected_args}

Correct behavior: {correct_behavior}
Bad behavior: {bad_behavior}

The model's actual response (including any tool calls made):
---
{response}
---

Score 0-100 using:
- 90-100: Perfect. Correct call/no-call decision, right tool, args are sensible and non-hallucinated.
- 70-89: Mostly correct. Right decision and tool, but args slightly off or unnecessary extras included.
- 40-69: Partial. Made a tool call when it shouldn't (or vice versa), OR picked a reasonable but wrong tool.
- 10-39: Poor. Wrong decision and wrong tool, or hallucinated args badly.
- 0-9: Completely wrong. Called a tool with nonsense args, or refused to call when clearly needed.

Return ONLY a JSON object:
{{"score": 85, "passed": true, "details": "Called run_tests with test_file='tests/test_auth.py', correct tool and reasonable path."}}

passed = true if score >= 70."""


def get_all_cases():
    """Return all cases as (prompt, case_meta) tuples."""
    return [(c["prompt"], c) for c in CASES]


def grade_case(case, response_text):
    """Returns the filled rubric string to send to the judge."""
    return JUDGE_RUBRIC.format(
        prompt=case["prompt"],
        should_call=case["should_call"],
        expected_tool=case["expected_tool"] or "None",
        expected_args=str(case["expected_args"]) if case["expected_args"] else "N/A",
        correct_behavior=case["correct_behavior"],
        bad_behavior=case["bad_behavior"],
        response=response_text,
    )
