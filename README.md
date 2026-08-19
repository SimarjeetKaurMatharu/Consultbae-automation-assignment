# ConsultBae — AI Automation Take-Home Assignment

This repository contains my completed submission for the AI Automation Take-Home Assignment. It includes a unified database pipeline, an n8n automation workflow, and a mini audio collection web application.

---

## 🚀 Setup & Installation Steps

### 1. Prerequisites
Ensure you have the following installed on your machine:
* Python 3.9+
* SQL Server / SSMS (or SQLite/Postgres based on destination configuration)
* n8n (Desktop app or Cloud account)

### 2. Task 1: Database & Ingestion Setup
1. Clone this repository:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd <YOUR_REPO_NAME>
   ```
2. Install the required dependencies:
   ```bash
   pip install pandas openpyxl
   ```
3. Run the ingestion script to clean and merge the 3 raw dataset sheets:
   ```bash
   python merge_pipeline.py
   ```
4. Execute the verification scripts inside **`database_queries.sql`** using SSMS to view data consistency anomalies.

### 3. Task 2: Running the n8n Automation
1. Open your n8n workspace dashboard.
2. Click **Import from File** and select the exported workflow JSON file from this repository.
3. Ensure your Google Sheets or Email Node credentials are fully updated before executing.

### 4. Task 3: Running the Audio Collection App
1. Navigate into your extracted frontend directory:
   ```bash
   cd audio-app
   ```
2. Install framework dependencies and spin up the web development server:
   ```bash
   npm install
   npm run dev
   ```
3. Open your web browser and navigate to the local environment link provided in your terminal (typically `http://localhost:5173`).

---

## 🛠️ Task 1 & Task 2: Core Engineering Summary

### Task 1 — Data Merge Pipeline
Because there was no single shared primary identifier across the files, I built an automated ingestion loop using **Pandas** and **SQL Server (SSMS)** to map workers cleanly. 
* The system checks three identity anchors: **Email**, **Name**, and **Phone Number**.
* Conflicting entries are isolated as `Unmatched` to protect data pools, while clean records are assigned a unified tracking string (`Candidate_ID`). 

### Task 2 — n8n Workflow Automation
I built a low-code processing flow inside **n8n** that evaluates incoming entries against our baseline data rules. 
* Eligible workers pass through a conditional branch filter.
* The system dynamically injects an operational priority tracker called `Candidate_Tier` (`Verified = Yes` becomes `Tier 1`, otherwise `Tier 2`).
* Sorted profiles are exported straight into Google Sheets, and a clean consolidated summary log is compiled.

---

## 📱 Task 3: Mini Audio Collection Application

### Architecture & Tech Stack
* **Frontend:** React.js, TypeScript, Tailwind CSS
* **Backend & Storage:** Supabase (PostgreSQL engine)
* **Audio Engineering:** Native Browser Web Audio API & MediaRecorder API

### Technical Implementation & Extraction Logic
To capture high-volume audio tracking metadata without overloading a traditional backend server, all heavy processing is calculated directly on the client side before database ingestion:
1. **Audio Extraction:** When a user records or uploads a file, it is decoded into an `AudioBuffer` via the browser's native Web Audio Context. This instantly exposes stable properties for `duration_sec` and `sample_rate_khz`.
2. **Loudness Calculation:** The application processes the raw floating-point amplitude channel streams. It calculates the Root Mean Square (RMS) of the signal values and converts it logarithmically into standard decibels (`20 * Math.log10(rms)`).
3. **Noise/Quality Estimator:** I designed a custom matrix that tracks the ratio of data silence against peak amplitudes. If the signal has low amplitude peaks but high frequency deviations, it flags the file as noisy, mapping it to descriptive quality tags.
4. **Cloud Pipeline:** Once analyzed, the raw file is streamed directly to a Supabase object storage bucket, and its calculated metadata parameters are written to the database using row-level security.

---

## 📊 Task 4: Data Quality & Issues Report

While working on the data, I found several problems in the three CSV files and the automation pipeline. Here is a list of the issues I discovered and how I fixed them:

* **Inconsistent Columns and Missing Data:** The columns in the three files did not match. Important information like `Rate`, `Status`, `Skill Tags`, `Verified`, and `Projects Completed` was blank (`NULL`) for some people. I designed a flexible database structure that uses default blank values instead of breaking the entire pipeline.
* **Difficulties Matching Candidates (No Common ID):** The files did not have a shared ID column. Checking only one field was risky due to spelling mistakes. I created a matching logic that checks three fields: **Email**, **Name**, and **Phone Number**. Confirmed matches are grouped together, while conflicting data is marked as `Unmatched` to avoid corrupting records.
* **Strict Filters Hidden Valid Data:** Initially, my automation filter only pulled records where `Match_Status = Confirmed AND Status = Active`. This caused valid candidates like Tanvi to drop out because her status was set to `Paused`. I updated the filter logic to properly include non-active states, successfully retaining the expected 11 final candidates.
* **Broken Date Formats:** Dates unexpectedly turned into raw Excel numbers like `46227` and `46253` during processing, breaking database sorting. I added a date-parsing function into my code to automatically convert these integers back into standard, readable ISO dates.
* **n8n Missing Sort Field:** The n8n Sort Node gave a `Couldn't find the field 'Projects Completed'` error even though the data was visible in the preview. I manually re-mapped the data paths inside the expressions panel and refreshed the input schema to fix it.
* **Workflow Stopped on Conditional Branches:** Nodes down the line threw a `Node was not executed` error when data took an alternate path at a true/false split. I adjusted the workflow logic to make sure the data routes safely through fallback paths so the pipeline never freezes.
* **Multiple Spam Emails for Shortlisted Candidates:** The final Email Node was executing separately for every single candidate row (e.g., sending 10 individual emails instead of 1 clean list). I added an **Item Lists (Aggregate) Node** right before the email step to combine all candidate rows into a single list, ensuring exactly one summary email is sent.
* **Missing Business Metrics:** The original files lacked a way to prioritize workers. I dynamically injected a new field called `Candidate_Tier` (`Verified = "Yes"` becomes `Tier 1`, otherwise `Tier 2`), allowing us to neatly sort the final 11 candidates straight into Google Sheets.

---

## 🪵 Stuck Log

### Challenge 1: The Email Node sent separate emails for every candidate instead of one list.
* **Where I got stuck:** After filtering candidates down to the final eligible records, n8n looped through the rows and tried to send a separate email for every single person, which would spam the inbox.
* **What I searched:** *"How to combine multiple rows into one email in n8n"*, *"n8n loop running email node multiple times"*
* **Suggestions I rejected and why:** I got suggested using a complex Code Node with custom JavaScript to write a `for` loop. I rejected this because the assignment strictly stated pure-code automation solutions score zero. I wanted to use native, no-code features.
* **How I got unstuck:** I discovered the **Item Lists Node** (using the Aggregate feature). I placed it right before the Email Node to group all individual candidate rows into a single list object. This forced n8n to send exactly one email containing the full list.

### Challenge 2: Date formats randomly broke and turned into weird numbers.
* **Where I got stuck:** The dates in the source files changed into raw numbers like `46227` during processing, which completely broke my database sorting.
* **What I searched:** *"Dates turning into 5 digit numbers in excel csv processing"*, *"convert excel serial date number to standard date"*
* **Suggestions I rejected and why:** I saw suggestions telling me to manually re-format the source CSV files in Excel. I rejected this because a real pipeline must handle raw, imperfect data automatically without human intervention.
* **How I got unstuck:** I realized Excel stores dates internally as serial integers. I added a conversion check directly into my script to automatically parse these numbers back into readable dates before saving them to the database.

### Challenge 3: n8n Sort Node gave a "Couldn't find the field" error for data I could clearly see.
* **Where I got stuck:** The Sort Node threw an error saying `Projects Completed` did not exist, even though it was clearly in the table preview.
* **What I searched:** *"n8n sort node error field not found visual data exists"*, *"schema drift in n8n nodes"*
* **Suggestions I rejected and why:** A forum post suggested deleting the node and recreating the whole workflow. I rejected this because it didn't solve the underlying problem and wasn't a reliable fix.
* **How I got unstuck:** I opened the expressions panel, manually re-mapped the incoming JSON path for `Projects Completed`, and forced the node to refresh its input data schema, which solved the error instantly.

---

## 📈 Task 5: Stretch Plan (Weekend Scale)
* If 5,000 workers open the app at the same time, the server might crash because a small local system cannot handle all those big audio files hitting it at once. To fix this, we should send the recordings directly to a giant cloud bucket like AWS S3 instead of saving them on our small server. Also, the database will definitely lock up and freeze if everyone tries to save their details at the exact same second. We can resolve this database traffic jam by setting up a queue system, which acts like a neat waiting line to process entries one by one. Finally, because many workers have bad phone internet, their uploads will probably break halfway through. To prevent them from losing their progress and starting over, we must use a smart resume feature that saves the uploaded data chunks and continues right from where it stopped.
