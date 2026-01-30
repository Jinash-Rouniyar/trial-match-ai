import pandas as pd
import os

AACT_DATA_DIR = './aact_data'
# The two trials we want for our fast demo
TARGET_NCT_IDS = ['NCT05943132', 'NCT06241142']

def create_demo_files():
    """
    Reads the _subset files and creates a tiny _demo file with only two trials.
    """
    print("--- Creating ultra-fast demo files ---")
    try:
        print("Loading subset files...")
        studies_subset = pd.read_csv(os.path.join(AACT_DATA_DIR, 'studies_subset.txt'), sep='|', low_memory=False)
        eligibilities_subset = pd.read_csv(os.path.join(AACT_DATA_DIR, 'eligibilities_subset.txt'), sep='|', low_memory=False)

        print(f"Filtering for just our 2 target trials: {', '.join(TARGET_NCT_IDS)}")
        studies_demo = studies_subset[studies_subset['nct_id'].isin(TARGET_NCT_IDS)]
        eligibilities_demo = eligibilities_subset[eligibilities_subset['nct_id'].isin(TARGET_NCT_IDS)]

        print("Saving new demo files...")
        studies_demo.to_csv(os.path.join(AACT_DATA_DIR, 'studies_demo.txt'), sep='|', index=False)
        eligibilities_demo.to_csv(os.path.join(AACT_DATA_DIR, 'eligibilities_demo.txt'), sep='|', index=False)
        
        print("\n--- Demo files created successfully! ---")
        print("Your 'aact_data' folder now contains 'studies_demo.txt' and 'eligibilities_demo.txt'.")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please make sure the '_subset.txt' files exist. Run 'create_subset.py' if needed.")

if __name__ == "__main__":
    create_demo_files()