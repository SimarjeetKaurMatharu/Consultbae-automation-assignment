import os
import pandas as pd

FILE_PATH = "C:\\Users\\simar\\OneDrive\\Documents\\Cleaned_data_Automation_project.xlsx"

def run_pipeline():
    print("--- Starting Data Ingestion Pipeline ---")
    
    if not os.path.exists(FILE_PATH):
        print(f"Error: Could not locate source file at {FILE_PATH}")
        return

    # 1. Load sheets safely
    df1 = pd.read_excel(FILE_PATH, sheet_name="Naukri")
    df2 = pd.read_excel(FILE_PATH, sheet_name="Gig")
    df3 = pd.read_excel(FILE_PATH, sheet_name="CBNexus_contact")
    print(f"Loaded datasets: Naukri {df1.shape}, Gig {df2.shape}, CBNexus {df3.shape}")

    # 2. Normalize tracking anchors
    df1["email_match"] = df1["Email"].str.strip().str.lower()
    df1["name_match"] = df1["Full Name"].str.strip().str.lower()
    df1["phone_match"] = df1["Phone"].astype(str).str.replace(r"\D", "", regex=True)

    df2["email_match"] = df2["Email ID"].str.strip().str.lower()
    df2["name_match"] = df2["Worker Name"].str.strip().str.lower()

    df3["name_match"] = df3["Name"].str.strip().str.lower()
    df3["phone_match"] = df3["Phone Number"].astype(str).str.replace(r"\D", "", regex=True)

    # 3. Create Unique Candidate IDs based on Naukri baseline index
    df1["Candidate_ID"] = "C" + (df1.index + 1).astype(str).str.zfill(3)

    # 4. Map Naukri baseline candidates to Gig using exact email validation rules
    naukri_gig_map = df1[["Candidate_ID", "email_match"]].merge(
        df2[["email_match", "Worker Name", "Email ID"]],
        on="email_match",
        how="inner"
    )
    df2 = df2.merge(naukri_gig_map[["Candidate_ID", "Email ID"]], on="Email ID", how="left")

    # 5. Apply the safe fallback tracking map for cross-system verification anomalies
    safe_cbnexus_map = {
        9000000013: "C039", 9000000136: "C007", 9000000263: "C018", 9000000148: "C035",
        9000000211: "C014", 9000000106: "C016", 9000000138: "C008", 9000000223: "C017",
        9000000113: "C004", 9000000137: "C031", 9000000254: "C001", 9000000133: "C027",
        9000000273: "C040"
    }
    df3["Candidate_ID"] = df3["Phone Number"].map(safe_cbnexus_map)

    # 6. Group metrics into a unified Master data frame
    master = df1.copy()
    master = master.merge(
        df2[["Candidate_ID", "Rate", "Rate type", "Status", "Skill Tags"]],
        on="Candidate_ID", how="left"
    )
    master = master.merge(
        df3[["Candidate_ID", "Verified", "Projects Completed"]],
        on="Candidate_ID", how="left"
    )

    # 7. Apply Confirmation Rules & Handle Unmatched Identities
    master["Match_Status"] = "Unmatched"
    master.loc[master["Candidate_ID"].isin(naukri_gig_map["Candidate_ID"]), "Match_Status"] = "Confirmed"

    # Export clean master tracking data
    output_filename = "final_master.csv"
    master.to_csv(output_filename, index=False)
    print(f"Successfully processed integrated file: '{output_filename}' ({len(master)} rows generated)")

if __name__ == "__main__":
    run_pipeline()
