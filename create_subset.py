import os
import json
import pandas as pd
import torch
from transformers import pipeline, AutoTokenizer, AutoModel, BitsAndBytesConfig
from torch.nn.functional import cosine_similarity
import warnings
import re
from tqdm import tqdm

# --- CONFIGURATION ---
AACT_DATA_DIR = './aact_data'
SYNTHEA_DATA_DIR = './synthea_data/json'
# === NEW: Define our two target trials ===
TARGET_NCT_IDS = ['NCT05943132', 'NCT06241142']

# --- STEP 1: LOAD MODELS ---
print("Loading models...")
HF_TOKEN = "" # <-- PASTE YOUR TOKEN
quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16)
model_id = "microsoft/Phi-3-mini-4k-instruct"
phi_tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
phi_tokenizer.pad_token = phi_tokenizer.eos_token
reasoning_pipeline = pipeline("text-generation", model=model_id, model_kwargs={"quantization_config": quantization_config}, device_map="auto", token=HF_TOKEN, tokenizer=phi_tokenizer)
embedding_tokenizer = AutoTokenizer.from_pretrained("michiyasunaga/BioLinkBERT-large")
embedding_model = AutoModel.from_pretrained("michiyasunaga/BioLinkBERT-large")
ner_pipeline = pipeline("ner", model="d4data/biomedical-ner-all", aggregation_strategy="simple")

# --- STEP 2: DATA PREPARATION (Completely new logic) ---
def load_target_trials_data():
    """
    Loads data for ONLY our two target clinical trials.
    """
    print(f"Loading data for {len(TARGET_NCT_IDS)} specific trials: {', '.join(TARGET_NCT_IDS)}")
    try:
        # We still need to load the full files to find our specific trials
        studies = pd.read_csv(os.path.join(AACT_DATA_DIR, 'studies_subset.txt'), sep='|', low_memory=False, on_bad_lines='skip')
        eligibilities = pd.read_csv(os.path.join(AACT_DATA_DIR, 'eligibilities_subset.txt'), sep='|', low_memory=False, on_bad_lines='skip')

        # Filter the dataframes to ONLY include our target trials
        target_studies_df = studies[studies['nct_id'].isin(TARGET_NCT_IDS)]
        target_eligibilities_df = eligibilities[eligibilities['nct_id'].isin(TARGET_NCT_IDS)]

        if len(target_studies_df) < len(TARGET_NCT_IDS):
            print("Warning: Not all target trials were found in the 'studies_subset.txt' file.")

        # Merge the two dataframes to get the criteria for our trials
        trials_to_analyze_df = pd.merge(target_studies_df, target_eligibilities_df, on='nct_id')
        
        return trials_to_analyze_df

    except FileNotFoundError as e:
        print(f"\nCRITICAL ERROR: {e}")
        print("Please make sure the '_subset.txt' files exist. Run 'create_subset.py' if needed.")
        return None

# --- STEP 3: FEATURE EXTRACTION (Unchanged) ---
def create_patient_profile(patient_file_path):
    with open(patient_file_path, 'r', encoding='utf-8') as f:
        try: patient_data = json.load(f)
        except json.JSONDecodeError: return {}
    if 'entry' not in patient_data: return {}
    profile = {"conditions": [], "medications": [], "text_summary": ""}
    full_text_narrative = []
    for entry in patient_data.get('entry', []):
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        if resource_type == 'Condition':
            condition_name = resource.get('code', {}).get('text', '')
            if condition_name: profile['conditions'].append(condition_name); full_text_narrative.append(f"Patient has a condition of {condition_name}.")
        elif resource_type == 'MedicationRequest':
            med_name = resource.get('medicationCodeableConcept', {}).get('text', '')
            if med_name: profile['medications'].append(med_name); full_text_narrative.append(f"Patient is prescribed {med_name}.")
    profile['text_summary'] = " ".join(full_text_narrative)
    if profile['text_summary']:
        entities = ner_pipeline(profile['text_summary'])
        profile['ner_entities'] = list(set([entity['word'] for entity in entities if 'word' in entity]))
    else:
        profile['ner_entities'] = []
    return profile

# --- STEP 4: LLM AND MATCHING LOGIC (Unchanged) ---
def parse_eligibility_criteria(criteria_text):
    prompt = f'[INST]Read the following eligibility criteria. Extract the key inclusion and exclusion criteria as a JSON object with keys "inclusion" and "exclusion". Do not add explanation. Criteria: "{text}"[/INST]'.replace('{text}', criteria_text[:8000])
    outputs = reasoning_pipeline(prompt, max_new_tokens=512, do_sample=False)
    generated_text = outputs[0]['generated_text']
    try:
        json_str = generated_text[generated_text.find('{'):generated_text.rfind('}')+1]
        return json.loads(json_str)
    except json.JSONDecodeError: return {"inclusion": [], "exclusion": []}

def get_embedding(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512).to(model.device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)

def calculate_match_score(patient_profile, trial_criteria):
    score, patient_full_text = 100.0, patient_profile.get('text_summary', '')
    if not patient_full_text: return 0.0
    patient_embedding = get_embedding(patient_full_text, embedding_tokenizer, embedding_model)
    if not trial_criteria.get('inclusion'): score -= 50
    else:
        for criterion in trial_criteria['inclusion']:
            criterion_embedding = get_embedding(criterion, embedding_tokenizer, embedding_model)
            if cosine_similarity(patient_embedding, criterion_embedding).item() < 0.6: score -= 15
    if trial_criteria.get('exclusion'):
        for criterion in trial_criteria['exclusion']:
            criterion_embedding = get_embedding(criterion, embedding_tokenizer, embedding_model)
            if cosine_similarity(patient_embedding, criterion_embedding).item() > 0.7: score = 0; break
        if score == 0: return 0.0
    return max(0, score)

# --- STEP 5: MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    trials_to_analyze_df = load_target_trials_data()
    if trials_to_analyze_df is None or trials_to_analyze_df.empty:
        print("Could not load the 2 target trials. Exiting.")
        exit()
    print(f"Successfully loaded {len(trials_to_analyze_df)} target trials. Pre-parsing their criteria...")

    # Pre-parse the criteria for our 2 trials once
    criteria_cache = {}
    for index, trial in trials_to_analyze_df.iterrows():
        criteria_cache[trial['nct_id']] = parse_eligibility_criteria(trial['criteria'])
    print("Criteria parsing complete.")

    try:
        patient_files = [f for f in os.listdir(SYNTHEA_DATA_DIR) if f.endswith('.json') and not f.startswith(('hospital', 'practitioner'))]
    except FileNotFoundError: patient_files = []
    
    if not patient_files: print("No patient files found.")
    else: print(f"Beginning analysis of {len(patient_files)} patients...")

    all_successful_matches = []

    for patient_file in tqdm(patient_files, desc="Screening Patients"):
        patient_profile = create_patient_profile(os.path.join(SYNTHEA_DATA_DIR, patient_file))
        if not patient_profile.get('conditions'): continue
        
        # For each patient, check against our 2 pre-parsed trials
        for nct_id, parsed_criteria in criteria_cache.items():
            if not parsed_criteria.get('inclusion'): continue
            
            score = calculate_match_score(patient_profile, parsed_criteria)
            
            # Use a higher threshold for a more meaningful demo
            if score > 65:
                # Find the title for the matching nct_id
                title = trials_to_analyze_df[trials_to_analyze_df['nct_id'] == nct_id]['brief_title'].iloc[0]
                
                # Check if this patient is already in our match list
                found_patient = next((item for item in all_successful_matches if item["patient_file"] == patient_file), None)
                
                if found_patient:
                    # Add trial to existing patient's list
                    found_patient['ranked_results'].append({"nct_id": nct_id, "title": title, "score": score})
                else:
                    # Add new patient to the list
                    all_successful_matches.append({
                        "patient_file": patient_file,
                        "conditions": patient_profile.get('conditions', []),
                        "ranked_results": [{"nct_id": nct_id, "title": title, "score": score}]
                    })

    # FINAL SUMMARY
    print("\n\n" + "#"*80)
    print("--- ✅ FINAL SUMMARY: Patients Matched to Target Trials ---")
    print("#"*80)
    if not all_successful_matches:
        print("\nNo patients from the cohort were a strong match for the 2 target trials.")
    else:
        # Sort results within each patient's list
        for match in all_successful_matches:
            match['ranked_results'] = sorted(match['ranked_results'], key=lambda x: x['score'], reverse=True)
            
        print(f"\nFound {len(all_successful_matches)} patients with potential matches!")
        for match_info in all_successful_matches:
            print(f"\n\n--- Patient: {match_info['patient_file']} ---")
            print(f"    Relevant Conditions: {', '.join(match_info['conditions'][:4])}...")
            print("    --- Matched Trials (Ranked) ---")
            for result in match_info['ranked_results']:
                print(f"      - ({result['score']:.0f}%) {result['nct_id']}: {result['title']}")