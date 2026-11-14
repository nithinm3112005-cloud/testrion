from PIL import Image
ASSETS = "/Users/darshan/Desktop/PROJECT 2/report/assets/"

def shot(B, key, file, caption, maxh=6.4, maxw=5.7):
    w, h = Image.open(ASSETS + file).size
    B.fig(key, file, caption, min(maxw, maxh * w / h))

def build(B, D):
    B.h1("SYSTEM DESIGN AND IMPLEMENTATION")
    B.p("The implementation is organised as a testing core and a supporting software platform. The core consists of the testing engine, the Auto-fix engine and the model registry, written in Python on top of scikit-learn. The platform around it provides user accounts, dataset and run management, a REST interface, a web application, a monitoring service and a command-line gate. The core was written so that it does not depend on the web server, which allows the same code to be used by the web application, the pytest suite, the CI workflow and the Streamlit interface.")
    B.h2("5.1 Hardware and Software Specifications")
    B.p("The platform was developed and measured on a single Apple laptop. {T:env} lists the environment. The application uses only free and open-source components and runs on a laptop without a database server, a GPU or Docker. The Dockerfile included in the repository packages the same application into one container, but it has not been built on the development machine because Docker is not installed there.")
    env = [
        ["Computer", "Apple laptop with the Apple M5 chip (10-core CPU), macOS"],
        ["Python runtime", "Python 3.9.6 (the CI workflow uses Python 3.10)"],
        ["JavaScript runtime", "Node.js v26.8.1, npm 11.19.0"],
        ["Front-end", "React 18.3, React Router 6.28, Vite 5.4, Recharts 2.14, lucide-react 0.468"],
        ["Back-end", "FastAPI 0.128.8, Uvicorn 0.39.0, Pydantic 2.13, python-multipart 0.0.20"],
        ["Machine learning", "scikit-learn 1.6.1, pandas 2.3.3, NumPy 2.0.2"],
        ["Database", "SQLite 3 (single file, standard-library driver)"],
        ["Testing and CI", "pytest 8.3.4, httpx, GitHub Actions (Ubuntu 22.04)"],
        ["Alternative interface", "Streamlit 1.50.0"],
        ["Browser used for UI verification", "Google Chrome (desktop and headless)"],
    ]
    B.table("env", "Documented software and hardware environment", ["Component", "Documented technology"], env, [2.0, 5.0], 10, bold_first=True)
    B.h2("5.2 System Architecture")
    B.p("The architecture is shown in {F:architecture}. The browser talks to a FastAPI server over JSON. The server authenticates the user, stores datasets, runs and prediction logs in SQLite, and calls the testing engine, the Auto-fix engine and the model registry. The testing engine contains the classification suite (`testing.py`), the regression suite (`regression.py`) and the shared generators for edge-case, adversarial, slice and fairness tests (`extras.py`). In production mode the same server also serves the compiled React application, so the complete product starts with one command.")
    B.fig("architecture", "fig_architecture.png", "High-level architecture of the Testrion platform", 5.4)
    B.h2("5.3 Back-end Modules")
    B.p("The back-end is a small number of focused Python modules ({T:modules}). All numerical work is delegated to scikit-learn, pandas and NumPy [17], [29], [30]. Because the engine is independent of the web layer, it can be executed from the command line (`ci_check.py`), from tests, from the evidence generator (`evidence.py`) and from the Streamlit application.")
    mods = [
        ["app/main.py", "FastAPI application: authentication, datasets, runs, Auto-fix, batch benchmarking, playground, model export, live monitoring and statistics; serves the built front-end."],
        ["app/auth.py", "Account creation, PBKDF2 password hashing, bearer-token sessions and the dependency that protects every endpoint."],
        ["app/db.py", "SQLite schema, migrations and all data-access functions."],
        ["app/datasets.py", "The five built-in datasets, their generators, column documentation, previews and dataset provenance."],
        ["app/models.py", "Registry of the twelve models, default settings, seeds and tuning grids."],
        ["app/testing.py", "Data preparation, task detection, the classification test suite, scoring, the deployment gate and final-model training."],
        ["app/regression.py", "The regression test suite (R², error metrics, target skew, valid predictions)."],
        ["app/extras.py", "Edge-case generation, adversarial perturbation search, slice testing and demographic parity."],
        ["app/fixer.py", "The three-stage Auto-fix engine."],
        ["tests/test_ml_pipeline.py", "Eleven automated tests of the platform (Chapter 12)."],
        ["ci_check.py, evidence.py", "Command-line deployment gate for CI; generator of evidence tables and benchmarks."],
        ["streamlit_app.py", "Alternative interface for entering inputs, predicting and viewing test results."],
    ]
    B.table("modules", "Back-end modules and their responsibilities", ["File", "Responsibility"], mods, [1.9, 5.1], 9.5, bold_first=True)
    B.h2("5.4 Front-end Modules")
    B.p("The front-end is a single-page React application built with Vite. It uses React Router for navigation, Recharts for charts and a shared stylesheet, so that all pages have the same black and violet appearance. Pages that need the server call it through a small API client that attaches the session token. The pages are described together with screenshots in Section 5.8.")
    B.h2("5.5 Database Design")
    B.p("Data is stored in a single SQLite file [36]. There are five tables, shown in {F:er}. The table `users` stores the account with a salted password hash; `sessions` stores the opaque bearer tokens; `datasets` stores the metadata of uploaded files (the files themselves are kept on disk under random identifiers); `runs` stores every test run with its summary columns and the complete result as JSON; and `prediction_log` stores each logged prediction for the monitoring service. Every row of `datasets`, `runs` and `prediction_log` carries the identifier of its owner, and every query filters on it.")
    B.fig("er", "fig_er.png", "Entity-relationship diagram of the SQLite database", 4.8)
    B.h2("5.6 REST Interface")
    B.p("The server exposes the endpoints in {T:api}. Everything except the health check and the two authentication calls requires a valid bearer token. Interactive documentation is generated automatically by FastAPI [32] at the path `/docs`.")
    api = [
        ["POST /api/auth/signup, /login, /logout; GET /api/auth/me", "Create an account, sign in, sign out, return the current user"],
        ["GET /api/models, /api/test-catalog", "List the twelve models (with their task) and the descriptions of all tests"],
        ["GET /api/datasets; POST /api/datasets", "List built-in and own datasets; upload a CSV file"],
        ["GET /api/datasets/{id}/preview, /download; DELETE", "Preview with data dictionary; CSV download; delete an upload"],
        ["POST /api/runs; GET /api/runs, /api/runs/{id}; DELETE", "Run the test suite; list and read runs; delete a run"],
        ["POST /api/runs/{id}/autofix", "Run the Auto-fix engine and store the fixed run"],
        ["GET /api/runs/{id}/schema; POST /predict", "Feature schema and a prediction for one row (also logged)"],
        ["GET /api/runs/{id}/export", "Download the trained pipeline as `model.pkl`"],
        ["GET, DELETE /api/runs/{id}/monitor; POST /simulate", "Drift and latency report; clear the log; replay normal or shifted traffic"],
        ["POST /api/batch", "Test several models of one task in parallel"],
        ["GET /api/stats, /api/health", "Dashboard statistics; liveness check"],
    ]
    B.table("api", "REST endpoints of the Testrion API", ["Endpoint", "Purpose"], api, [3.1, 3.9], 9)
    B.h2("5.7 Authentication and Data Isolation")
    B.p("Passwords are never stored. At sign-up a random 16-byte salt is generated and the password is hashed with PBKDF2-HMAC-SHA256 and 200,000 iterations [31]; at sign-in the hash is recomputed and compared in constant time, and the same error message is returned for an unknown e-mail address and for a wrong password. A successful sign-in creates a random 32-byte URL-safe token that is stored in the `sessions` table and expires after seven days. Every protected endpoint resolves the token to a user and filters all data by that user, so one user cannot read, run or delete another user's datasets, runs or predictions; this behaviour is verified by an automated test. User-supplied pipeline options are validated against a whitelist before use, uploaded files are restricted to CSV files of at most 10 MB, and model export uses the standard Python `pickle` format [37] (a pickle file must only be loaded from a trusted source).")
    B.h2("5.8 User Interface Walkthrough")
    B.p("This section shows the application as it is used. Every figure is a real screenshot of the running system; where two screens are shown in one figure, the caption names them from left to right.")
    B.h3("5.8.1 Landing page, sign-in, dashboard and datasets")
    B.p("The public landing page (left of {F:ui_c1}) introduces the product on a starfield background with a violet planet rim; below it come the features, the three-step process, the five test dimensions, a short FAQ and a sign-up card. The sign-in page (right) shares the same theme and offers a one-click demo account. After signing in, the dashboard (left of {F:ui_c2}) shows the number of runs, the average score, the tests passed, the issues found, the number of automatic fixes and the average improvement, together with a score trend and the one-click demonstration button. The Datasets page (right) lists the eleven datasets with their origin, size and tags; each can be previewed with its data dictionary or downloaded as CSV, and own files can be uploaded.")
    B.fig("ui_c1", "ui_c1.png", "Landing page (left) and sign-in page (right)", 5.7)
    B.fig("ui_c2", "ui_c2.png", "Dashboard (left) and Datasets page (right)", 5.7)
    B.h3("5.8.2 Starting a test and reading the report")
    B.p("The New Test wizard (left of {F:ui_c3}) first asks for a dataset, then for the column to predict. Columns that cannot be predicted are greyed out, and the task (classification or regression) is shown for each valid column; the next step selects a model that fits the task and offers advanced options such as imputation, scaling, class balancing, log-transform and protected attributes, or a parallel benchmark. The report opens with the deployment gate. The right side of {F:ui_c3} shows a run that the gate blocked, with the failed checks highlighted, and {F:ui_report_gate} shows an Auto-fixed run with the approved gate, the before-and-after score, the numbered repairs with their reasons and the tests whose status changed. Below the gate, the report lists the outcome counts, the score by category and every test; each test can be expanded to see the finding and the recommended fix.")
    B.fig("ui_c3", "ui_c3.png", "New Test wizard (left) and a blocked run before Auto-fix (right)", 5.7)
    shot(B, "ui_report_gate", "ui_report_gate.png", "Report of an Auto-fixed run: deployment gate and repair report", 4.9, 4.4)
    B.h3("5.8.3 Report tabs, playground and monitoring")
    B.p("The Model performance tab (left of {F:ui_c4}) shows the regression metrics, the actual-versus-predicted chart, the residual distribution, the comparison table of actual and predicted values, the feature importance and the generalisation summary. For classification (right of {F:ui_c4}) it shows precision, recall and F1 per class with their macro and weighted averages, the per-class chart, the confusion matrix and the data-slice results for the protected attributes. The Data profile and Configuration tabs show the dataset statistics and the pipeline settings that produced the run. The Try the model tab (left of {F:ui_c5}) lets the user enter feature values and obtain a prediction; for classification the class probabilities are shown, and each prediction is logged. The Live monitoring tab (right of {F:ui_c5}) shows the number of logged predictions, the average and 95th-percentile latency, the drift status and the time needed to compute it, the feature-drift chart with its thresholds, the latency series and the most recent predictions. In the figure, shifted traffic has made the area, bedroom, bathroom and region features cross the drift threshold.")
    B.fig("ui_c4", "ui_c4.png", "Model performance tab for a regression run (left) and a classification run with slices (right)", 5.7)
    B.fig("ui_c5", "ui_c5.png", "Try the model tab (left) and live monitoring after replaying shifted traffic (right)", 5.7)
    B.h3("5.8.4 Comparison, benchmarking, history and requirements")
    B.p("Two runs can be compared side by side (left of {F:ui_c6}): scores, metrics, category scores and the status of every test. The model-benchmark button tests all models of a task concurrently and ranks them on the leaderboard (right of {F:ui_c6}). The Test History page lists every run and allows two runs to be selected for comparison, and the Requirements page maps each requirement of the project specification to the feature that implements it.")
    B.fig("ui_c6", "ui_c6.png", "Run comparison (left) and leaderboard of models tested in parallel (right)", 5.7)
    B.h2("5.9 Use Case Description")
    B.p("The main actor is the user, who may be a student, a data scientist or a reviewer. The user signs in, uploads or chooses a dataset, configures and starts a run, reviews the report and the deployment decision, starts Auto-fix when the model is blocked, tries the model, watches live predictions for drift, compares runs or benchmarks models, and downloads the model. The system validates every input, runs the engines, stores the results and presents them ({F:usecase}).")
    B.fig("usecase", "fig_usecase.png", "High-level use cases of Testrion", 4.8)
    B.h2("5.10 Security and Operational Considerations")
    B.p("Testrion is designed for local use by one organisation. The current implementation protects its endpoints with authentication, isolates users' data, hashes passwords with a salted key-derivation function, restricts uploads and whitelists configuration. It does not claim to be a hardened public multi-tenant service: it has no password-reset or e-mail verification flow, no login rate limiting, no sandboxing of untrusted model files, and it uses the development server and SQLite. Chapter 13 discusses these limits together with the threats against the platform and against the models that it tests.")
