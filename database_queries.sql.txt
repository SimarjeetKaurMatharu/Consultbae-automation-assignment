-- ConsultBae AI Automation Assignment — Task 1 Database Code
-- Target Database: SQL Server (SSMS)
-- Description: Database creation, data schema validation, quality checks, 
--              and recruitment tiering queries.

-- 1. DATABASE INITIALIZATION
CREATE DATABASE CandidateDB;
GO
USE CandidateDB;
GO

-- 2. SCHEMA EXAMINATIONS & INITIAL ROW VERIFICATIONS
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';

SELECT COUNT(*) AS Total_Rows FROM final_master;

SELECT * FROM final_master;

SELECT 
    COUNT(*) AS Total_Rows,
    COUNT(DISTINCT Candidate_ID) AS Unique_Candidates
FROM final_master;

-- 3. IDENTITY INTEGRITY & DUPLICATE IDENTIFICATION DETECTORS
-- Check for duplicate IDs
SELECT Candidate_ID, COUNT(*) AS Duplicate_ID_Count
FROM final_master
GROUP BY Candidate_ID
HAVING COUNT(*) > 1;

-- Check for duplicate Emails
SELECT Email, COUNT(*) AS Duplicate_Email_Count
FROM final_master
GROUP BY Email
HAVING COUNT(*) > 1;

-- Check for duplicate Phone numbers
SELECT Phone, COUNT(*) AS Duplicate_Phone_Count
FROM final_master
GROUP BY Phone
HAVING COUNT(*) > 1;

-- Check for duplicate names
SELECT Full_Name, COUNT(*) AS Duplicate_Name_Count
FROM final_master
GROUP BY Full_Name
HAVING COUNT(*) > 1;

-- Check for orphan rows missing unique keys
SELECT * FROM final_master WHERE Candidate_ID IS NULL;


-- 4. LOGICAL ANOMALY & NEGATIVE VALUE PATROL
-- Identify negative experience data
SELECT * FROM final_master WHERE Experience_Years < 0;

-- Identify unrealistic experience bounds 
SELECT * FROM final_master WHERE Experience_Years > 50;

-- Identify negative commercial rates
SELECT * FROM final_master WHERE Rate < 0;

-- Identify negative financial compensation
SELECT * FROM final_master WHERE Current_CTC < 0;

-- Audit categorical inconsistencies
SELECT DISTINCT Status FROM final_master;
SELECT DISTINCT Rate_type FROM final_master;


-- 5. DATA CLEANING & RE-FORMATTING PHASES
-- Standardize and round fractional work experience
UPDATE final_master
SET Experience_Years = ROUND(Experience_Years, 1);

SELECT Full_Name, Experience_Years FROM final_master;


-- 6. MATCH COMPLETION AUDIT & METRICS 
SELECT 
    Match_Status,
    COUNT(*) AS Candidate_Count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM final_master), 2) AS Percentage
FROM final_master
GROUP BY Match_Status;

-- Isolate matched business operational users
SELECT
    Candidate_ID, Full_Name, Email, Phone, Rate, Status, Verified, Projects_Completed
FROM final_master
WHERE Match_Status = 'Confirmed'
ORDER BY Candidate_ID;

-- Isolate mismatched users for review
SELECT
    Candidate_ID, Full_Name, Email, Phone, City, Experience_Years, Current_CTC
FROM final_master
WHERE Match_Status = 'Unmatched'
ORDER BY Candidate_ID;


-- 7. DEMOGRAPHIC & SKILL DISTRIBUTION INSIGHTS
-- Top locations sorted by average compensation package
SELECT
    City,
    COUNT(*) AS Candidates,
    ROUND(AVG(Current_CTC), 0) AS Avg_CTC
FROM final_master
GROUP BY City
ORDER BY Avg_CTC DESC;

-- Average experience matrix grouped by territory
SELECT
    City,
    AVG(Experience_Years) AS Avg_Experience
FROM final_master
GROUP BY City
ORDER BY Avg_Experience DESC;

-- Consolidated demographic analytics leaderboard
SELECT
    City,
    COUNT(*) AS Candidate_Count,
    ROUND(AVG(Experience_Years), 1) AS Avg_Experience,
    ROUND(AVG(Current_CTC), 0) AS Avg_CTC
FROM final_master
GROUP BY City
ORDER BY Candidate_Count DESC;

-- Regional system verification and confirmation ratios
SELECT
    City,
    COUNT(*) AS Total_Candidates,
    SUM(CASE WHEN Match_Status = 'Confirmed' THEN 1 ELSE 0 END) AS Confirmed_Candidates,
    ROUND(SUM(CASE WHEN Match_Status = 'Confirmed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS Confirmation_Rate
FROM final_master
GROUP BY City
ORDER BY Confirmation_Rate DESC;

-- Tokenize and extract unstructured tag arrays from text fields
SELECT
    LTRIM(RTRIM(value)) AS Skill,
    COUNT(*) AS Candidate_Count
FROM final_master
CROSS APPLY STRING_SPLIT(Skill_Tags, ',')
WHERE Skill_Tags IS NOT NULL
GROUP BY LTRIM(RTRIM(value))
ORDER BY Candidate_Count DESC;


-- 8. TALENT COMPENSATION & OPERATIONAL METRICS
SELECT Verified, COUNT(*) AS Candidate_Count FROM final_master GROUP BY Verified;

SELECT Status, COUNT(*) AS Candidate_Count, ROUND(AVG(Rate), 2) AS Avg_Rate
FROM final_master
WHERE Status IS NOT NULL
GROUP BY Status
ORDER BY Candidate_Count DESC;

SELECT TOP 10 Candidate_ID, Full_Name, City, Experience_Years, Rate, Rate_type
FROM final_master
WHERE Rate IS NOT NULL
ORDER BY Rate DESC;


-- 9. RECRUITMENT RANKING & BUSINESS TIERS
-- Identify top tier workers sorted by background performance metrics
SELECT
    Candidate_ID, Full_Name, City, Experience_Years, Verified, Projects_Completed
FROM final_master
WHERE Verified = 'Yes'
ORDER BY Projects_Completed DESC;

-- Apply multi-conditional filters for active confirmed users
SELECT
    Candidate_ID, Full_Name, City, Experience_Years, Rate, Status, Verified, Projects_Completed
FROM final_master
WHERE Match_Status = 'Confirmed'
  AND Status = 'Active'
  AND Verified = 'Yes'
ORDER BY Projects_Completed DESC, Experience_Years DESC;


-- 10. RECRUITER VIEW DESIGN & PRIORITIZATION REPORT
-- Dynamically inject operational business tiering categorizations
CREATE VIEW Recruiter_Candidate_Shortlist AS
SELECT
    Candidate_ID,
    Full_Name,
    City,
    Experience_Years,
    Rate,
    Rate_type,
    Status,
    Verified,
    Projects_Completed,
    CASE 
        WHEN Verified = 'Yes' THEN 'Tier 1 - Verified'
        ELSE 'Tier 2 - Needs Verification'
    END AS Candidate_Tier
FROM final_master
WHERE Match_Status = 'Confirmed'
  AND Status = 'Active';
GO

-- Query the production view summary interface
SELECT * 
FROM Recruiter_Candidate_Shortlist
ORDER BY 
    Candidate_Tier ASC, 
    Projects_Completed DESC, 
    Experience_Years DESC;
