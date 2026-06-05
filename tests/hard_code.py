"""
Hard Code Challenges
--------------------
Brutal code problems — concurrency bugs, security holes, and algorithmic traps.
These require genuine understanding, not pattern matching on common Python gotchas.
"""

TEST_ID = "hard_code"
TEST_NAME = "Hard Code Challenges"
GRADING = "llm_judge"
TEST_DESCRIPTION = "Concurrency bugs, security holes, and algorithmic traps — require genuine code reasoning not memorization"

CHALLENGES = [
    {
        "id": "threading_race_condition",
        "prompt": """This code is supposed to safely increment a counter from multiple threads. A senior dev reviewed it and said it looks fine because it uses a lock. Find the bug, explain exactly why it fails despite the lock, predict what happens at runtime, and provide the correct fix.

````````python
import threading

counter = 0
lock = threading.Lock()

def increment(n):
    for _ in range(n):
        with lock:
            temp = counter
        counter = temp + 1

threads = [threading.Thread(target=increment, args=(100000,)) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)  # Expected: 400000. What actually happens?
```````""",
        "correct_answer": "The bug is that the lock is released between reading counter and writing counter+1. The with lock block only covers temp = counter, then the lock is released, then counter = temp + 1 happens outside the lock. This is a classic read-modify-write race condition. Multiple threads can read the same value of counter, all compute temp+1 with the same base, and all write the same incremented value, losing increments. The actual output will be far less than 400000, non-deterministic, varying each run. Fix: move counter = temp + 1 inside the with lock block, or use counter += 1 inside the lock.",
        "expected_key_steps": [
            "identifies that counter = temp + 1 is outside the lock",
            "explains read-modify-write race condition",
            "predicts output will be less than 400000 and non-deterministic",
            "correct fix moves the write inside the lock"
        ],
        "distractor_answer": "Says the code is correct because it uses a lock, or says the bug is using threading instead of multiprocessing, missing that the write is outside the lock scope.",
        "correct_behavior": "Spots that only the read is locked not the write, explains race condition, predicts non-deterministic low count, fixes by including write in lock scope.",
        "bad_behavior": "Says code is correct, blames wrong line, or gives fix that still has the race condition.",
    },
    {
        "id": "sql_injection_subtle",
        "prompt": """This Python function queries a database for a user by username. A security review passed it as safe because it uses parameterized queries. But there is still a critical security vulnerability. Find it, explain exactly how an attacker would exploit it, and provide the secure fix.

``````python
import sqlite3

def get_user_orders(username: str, order_status: str = None):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    base_query = "SELECT * FROM orders WHERE username = ?"
    params = [username]
    
    if order_status:
        base_query += f" AND status = '{order_status}'"
    
    cursor.execute(base_query, params)
    return cursor.fetchall()

# Called from web API:
# GET /orders?username=alice&status=pending
`````""",
        "correct_answer": "The username parameter is safely parameterized, but order_status is directly interpolated via f-string when provided, creating a SQL injection vulnerability despite the partial parameterization. An attacker can pass order_status='' OR '1'='1 to get all orders for all users, or order_status='' UNION SELECT username,password,null,null FROM users-- to extract the users table. The fix is to also parameterize order_status: append AND status = ? to base_query and add order_status to params list.",
        "expected_key_steps": [
            "identifies order_status f-string interpolation as the vulnerability",
            "explains username is safe but order_status is not",
            "provides concrete exploit example",
            "correct fix parameterizes order_status"
        ],
        "distractor_answer": "Says the code is safe because it uses parameterized queries, missing that only username is parameterized and order_status is not.",
        "correct_behavior": "Identifies the f-string interpolation of order_status, gives concrete exploit, fixes by adding order_status to params.",
        "bad_behavior": "Says code is safe, only mentions generic SQL injection without identifying the specific vulnerable line, or gives incomplete fix.",
    },
    {
        "id": "algorithmic_complexity_trap",
        "note": "[bold green]⚠ Hidden O(n³) — most models miss the third factor entirely[/bold green]",
        "prompt": """This function finds all duplicate values in a list and returns them. It works correctly on all test cases. However it has a severe performance bug that makes it unusable on large inputs. Identify the exact complexity, explain why it is wrong, provide the correct O(n) implementation, and explain what the correct implementation does differently.

````python
def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return duplicates

# Works correctly:
print(find_duplicates([1, 2, 3, 2, 4, 3, 5]))  # [2, 3]
print(find_duplicates([1, 1, 1, 1]))             # [1]
```""",
        "correct_answer": "The function is O(n^3) not O(n^2) as it appears. The outer two loops are O(n^2), but the lst[i] not in duplicates check is O(k) where k is the length of duplicates, making worst case O(n^3). On a list of 10000 elements this could be 10^12 operations. The correct O(n) implementation uses a dict or Counter to count occurrences in one pass, then returns elements with count > 1. Example: from collections import Counter; return [x for x, count in Counter(lst).items() if count > 1]. This is O(n) time and O(n) space.",
        "expected_key_steps": [
            "identifies actual complexity as O(n^3) not O(n^2)",
            "explains the not in duplicates check adds a third O(k) factor",
            "provides correct O(n) solution using dict or Counter",
            "explains why the O(n) solution works differently"
        ],
        "distractor_answer": "Says it is O(n^2) from the nested loops, missing the O(k) not-in check, or provides O(n log n) sort-based solution claiming it is O(n).",
        "correct_behavior": "Correctly identifies O(n^3), explains the hidden third factor, gives O(n) Counter solution, explains the difference.",
        "bad_behavior": "Says O(n^2), misses the not-in check cost, gives O(n log n) solution and claims it is O(n), or gives correct complexity without fixing it.",
    },
]


def get_prompt(challenge_index=0):
    challenge = CHALLENGES[challenge_index % len(CHALLENGES)]
    return challenge["prompt"], challenge


def get_all_prompts():
    return [(c["prompt"], c) for c in CHALLENGES]


JUDGE_RUBRIC = """You are evaluating whether an AI model correctly identified and fixed a brutal code challenge.

The challenge:
{prompt}

Correct answer:
{correct_answer}

Key steps the model MUST hit:
{expected_key_steps}

Common wrong answer:
{distractor_answer}

Correct behavior: {correct_behavior}
Bad behavior: {bad_behavior}

Model response:
---
{response}
---

Score 0-100. Be brutal:
- 90-100: Hits ALL key steps. Correct identification, correct explanation, correct fix, concise.
- 75-89: Correct bug and fix but misses one key step or explanation gap.
- 50-74: Identifies the right area but wrong root cause or incomplete fix.
- 20-49: Partially correct but significant conceptual errors.
- 0-19: Wrong bug, wrong fix, or says code is correct when it is not.

passed = true if score >= 70.
Return ONLY JSON: {{"score": 78, "passed": true, "details": "Identified race condition and fixed it but missed explaining the non-deterministic output prediction."}}"""


def grade_challenge(challenge, response_text):
    return JUDGE_RUBRIC.format(
        prompt=challenge["prompt"],
        correct_answer=challenge["correct_answer"],
        expected_key_steps="\n".join(f"- {s}" for s in challenge["expected_key_steps"]),
        distractor_answer=challenge["distractor_answer"],
        correct_behavior=challenge["correct_behavior"],
        bad_behavior=challenge["bad_behavior"],
        response=response_text,
    )
