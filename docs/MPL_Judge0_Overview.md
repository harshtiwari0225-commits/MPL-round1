# Judge0 — Working, Workflow, and Implementation

Companion to `MPL_Final_Backend_Plan.md`. Covers the code sandbox only. Game rules, pages, and admin privileges live in the plan. Formal reference. No implementation code.

---

## 1. Purpose

The event requires untrusted student code to be compiled and executed against hidden test cases. That work must not run inside the FastAPI process or on the same operating-system user that holds PostgreSQL.

Judge0 is the isolated execution service used for that purpose. It is not the contest platform. It does not know teams, scores, challenges, or bidding. It only answers one question: what happened when this program ran?

---

## 2. What Judge0 is

Judge0 is an open-source online code execution system (Community Edition, GPL-3.0). It exposes a JSON HTTP API. A client submits source code, a language identifier, optional standard input, optional expected output, and resource limits. Judge0 compiles and runs the program in a sandbox and returns a structured verdict.

Typical uses: competitive programming sites, e-learning platforms, recruitment tests, and in-browser editors.

Two flavours exist:

| Flavour | Role |
|---|---|
| **Judge0 CE** | Core language set (C, C++, Python, Java, JavaScript, and others). This is the flavour we use. |
| **Judge0 Extra CE** | Additional, less common languages. Not required for this event. |

Two ways to consume it:

| Mode | Meaning |
|---|---|
| **Self-hosted** | Official Docker Compose stack on our VPS. Unlimited submissions. This is the event-day choice. |
| **Hosted (RapidAPI)** | Public instance, billed per submission or by monthly plan. Acceptable only for local development. |

Official documentation: [ce.judge0.com](https://ce.judge0.com/). Source: [github.com/judge0/judge0](https://github.com/judge0/judge0).

---

## 3. How Judge0 works

### 3.1 Components (self-hosted)

A standard Judge0 deployment is several containers:

- **API** — accepts HTTP requests, writes a submission row, returns a token.
- **Workers** — dequeue submissions and execute them.
- **PostgreSQL** — Judge0's own submission store (separate from the MPL database).
- **Redis** — Judge0's internal job queue.
- **Isolate sandbox** — Linux namespaces and cgroups. Enforces CPU time, wall time, memory, process count, and output size. The submitted program cannot see the host filesystem or, if configured correctly, the network.

The MPL FastAPI service is a *client* of this stack. It is not part of it.

### 3.2 Execution of one submission

1. Client `POST /submissions` with `source_code`, `language_id`, `stdin`, optional `expected_output`, and limits.
2. API persists the job and returns `{ "token": "…" }`. Status is **In Queue** (id 1).
3. A worker claims the job. Status becomes **Processing** (id 2).
4. Isolate compiles the program (if the language requires it) and runs it with the given stdin and limits.
5. If `expected_output` was supplied, Judge0 compares it with stdout.
6. Result fields are stored: `status`, `stdout`, `stderr`, `compile_output`, `time`, `memory`.
7. Client `GET /submissions/{token}` until status id is greater than 2.

Optional variants:

- `wait=true` — block until finished and return the result in the POST response. Convenient, but ties up an HTTP connection. Use only on a self-hosted instance we control, and only for short limits.
- `POST /submissions/batch` — several test cases in one request.
- Callback URL — Judge0 can POST the result to our API when done (webhook). Useful so we do not poll.

### 3.3 Status identifiers

| Id | Description | Scoring consequence in MPL |
|---|---|---|
| 1 | In Queue | None. Still waiting. |
| 2 | Processing | None. Still running. |
| 3 | Accepted | Only this id may award points. |
| 4 | Wrong Answer | No points. |
| 5 | Time Limit Exceeded | No points. |
| 6 | Compilation Error | No points. |
| 7–12 | Runtime Error (various signals) | No points. |
| 13 | Internal Error | No points. Retry or hold. Do not treat as a fail of the team. |
| 14 | Exec Format Error | No points. |

Wrong Answer is produced only when `expected_output` was sent and stdout differs. If we omit `expected_output`, a clean run is reported as Accepted even if the answer is wrong. Therefore **our backend must always send expected output for official submits**.

---

## 4. Overall workflow in this project

Judge0 never faces the browser. Hidden tests never leave our API.

```
Team browser
    │  POST /submissions   { question_id, language, source_code }
    ▼
MPL FastAPI
    │  1. Authenticate member. Check clock, remaining time, rate limit.
    │  2. Load hidden tests from PostgreSQL. Never return them.
    │  3. Insert attempt row: status = queued.
    │  4. Forward source + each hidden test to Judge0.
    │  5. Collect verdicts. First failure stops the run.
    │  6. If every test is Accepted → apply the arena scoring rule.
    │  7. Commit PostgreSQL → update Redis → broadcast WebSocket.
    ▼
Judge0 (internal network only)
    sandbox run → token → status / stdout / time / memory
```

The same judge path serves all three arenas. Only the scoring rule changes after an Accepted verdict:

| Arena | On Accepted | On any other final status |
|---|---|---|
| Main (Debug / Math / Hard) | That question's points → `score_main` | 0 |
| Challenge pit | Winner: configured points and time. First Accepted closes the pit. | 0. Status 13 does not close the pit. |
| Bidding award | Configured easy / mid / hard points → `score_bidding` | 0. Time delta was already applied at award. |

**Run** (sample I/O only) uses the same Judge0 call but never writes score. **Submit** uses hidden tests and may write score.

If Judge0 is unreachable: the attempt remains `queued`, the team sees "judging…", and the event clock, bidding, and challenges continue. Judging is isolated from the rest of the game.

---

## 5. Benefits

1. **Isolation.** Student code does not execute in the FastAPI worker or as the database user.
2. **Language coverage.** One integration covers C, C++, Python, Java, and any other language we choose to allow.
3. **Resource limits.** CPU, wall clock, memory, and output size are enforced per submission. A tight loop cannot stall the VPS.
4. **Small integration surface.** Two HTTP endpoints. No need to maintain compilers, jails, or language images ourselves.
5. **Cost, if self-hosted.** No per-submission fee. Adequate for an estimated 1 000–3 000 runs in two hours.
6. **Separation of concerns.** Judge0 returns a mechanical verdict. MPL rules (pits, bid awards, remaining time, configured points) stay in our code.
7. **Failure isolation.** A Judge0 outage pauses judging only.

---

## 6. Limitations

1. **Not a contest engine.** No teams, no leaderboard, no hidden-test bank, no partial scoring policy. We own all of that.
2. **Stdout comparison is exact.** Trailing spaces, extra newlines, or different float formatting produce Wrong Answer unless we normalise output before compare, or we write tests to a strict format and document it.
3. **Single-process, stdin/stdout model.** Unsuitable for GUI programs, network servers, or multi-step interactive judges without extra work. MPL questions must be written as stdin → stdout.
4. **Self-host requires privileged Docker.** Isolate needs Linux cgroups and namespaces. The official compose file uses a privileged container. Use Judge0 **v1.13.1 or newer** (sandbox-escape issues were patched at 1.13.1). Disable network inside the sandbox. Do not publish Judge0's port to the public internet; bind it to the Docker network and let only FastAPI call it.
5. **Shared host kernel.** Isolation is process-level, not a microVM. Acceptable for a supervised campus event. Not a claim of military-grade tenancy.
6. **Hosted RapidAPI is a poor event-day dependency.** Rate limits, per-call cost, and an extra network hop. A free or basic hosted tier will not absorb this event's volume.
7. **Latency and queueing.** Each test is a compile-and-run. Many hidden tests, or a burst of submits, add seconds. The UI must show a judging state. A submit cooldown (about 10–15 seconds per question) is required.
8. **Internal Error (status 13)** is our problem, not the team's. Do not close a pit or award a rival on a Judge0 crash. Rejudge.
9. **No project/IDE features.** No multi-file workspaces, debuggers, or package installs beyond what the language image already contains.
10. **GPL-3.0.** Self-hosting and calling the API is fine. Shipping a modified Judge0 as a closed product has licence implications. We will consume it as an unmodified service.

---

## 7. Implementation idea

### 7.1 Placement

Add the official Judge0 Compose services to the same stack as FastAPI, MPL PostgreSQL, and Redis. Judge0 listens on an internal hostname, for example `http://judge0:2358`. Nginx does not proxy that port to the public internet.

FastAPI is the only process allowed to call Judge0. The browser calls FastAPI only.

### 7.2 Data we store (MPL database, not Judge0)

For each question:

- public prompt and sample I/O
- hidden tests: ordered list of `{ stdin, expected_stdout }`
- `language_ids` allowed
- `cpu_time_limit`, `memory_limit`
- points, arena, assignment (per-team for main; shared for challenge/bidding)

For each attempt:

- team, member, question, source, language
- Judge0 token(s)
- per-test status
- final verdict
- points awarded (0 or the rule amount)
- timestamps

### 7.3 Backend procedure on Submit

1. Reject if the event is over, the team has no remaining time, or the per-question cooldown has not elapsed (HTTP 429).
2. Persist the attempt as `queued`.
3. For each hidden test, `POST` to Judge0 with source, `language_id`, `stdin`, `expected_output`, and the question's limits. Stop at the first non-Accepted result.
4. Map Judge0 status ids to our verdict enum.
5. If all tests are Accepted, apply the arena scoring rule inside a PostgreSQL transaction.
6. Update the Redis leaderboard snapshot and remaining-time key if needed.
7. Broadcast the team verdict and, on a score change, the global board.

**Run** follows steps 2–4 against sample I/O only and never enters step 5.

### 7.4 Waiting for results

Preferred on a self-hosted instance: poll `GET /submissions/{token}` every 300–500 ms, with a hard timeout slightly above the wall-clock limit. Alternative: Judge0 callback into an internal FastAPI route. Do not use long `wait=true` on a hosted RapidAPI plan.

### 7.5 Output comparison

Decide one policy and publish it to teams:

- either tests demand exact stdout (simplest; document "no extra spaces or blank lines"), or
- the backend trims trailing whitespace per line before comparing, and still sends the normalised string as `expected_output`.

Do not leave this implicit.

### 7.6 Security controls

- Judge0 port closed to the campus network.
- Sandbox network disabled.
- Image pinned to **v1.13.1+**.
- Authentication token set on the Judge0 API (`X-Auth-Token`) even though it is internal.
- Hidden tests selected only on the server.
- Source size cap and submit rate limit in FastAPI, in addition to Judge0's own limits.

### 7.7 Failure policy

| Condition | Behaviour |
|---|---|
| Judge0 unreachable | Attempt stays queued. Team sees "judging…". Clock and other arenas continue. Admin is notified. |
| Status 13 (internal) | No score change. Eligible for admin rejudge. |
| Event hard-stop at 120:00 | New submits rejected. In-flight Judge0 jobs may finish but must not write points after the cutoff. |

### 7.8 Effort

The Judge0 client in FastAPI is approximately one day's work: language map, submit/poll, status mapping, batching of hidden tests.

Work that is not Judge0, and is larger:

- question bank and hidden tests
- arena scoring rules
- editor UI (Monaco or CodeMirror; not a full IDE)
- event-day operations (health check, rejudge)

---

## 8. Decision

| Item | Decision |
|---|---|
| Product | Judge0 CE, self-hosted, v1.13.1 or newer |
| Network | Internal Docker network only |
| Hosted RapidAPI | Development optional; not used on event day |
| Browser access | None |
| Official submit | Always send `expected_output` for every hidden test |
| Sample run | Judge0, no score |
| Points | Awarded only on status id 3 for every hidden test, then by arena rule |
| IDE | Not built. Contest console with a code editor component only |

Judge0 is the sandbox. The MPL backend remains the authority for every game rule.
