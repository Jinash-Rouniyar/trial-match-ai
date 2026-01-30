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
NUM_RANDOM_TRIALS = 5 # Set how many random trials to pick each run

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

# --- STEP 2: DATA PREPARATION ---
def load_random_trials_data(num_trials=5):
    """
    Loads the AACT subset and selects a random sample of trials to analyze.
    """
    print(f"Loading from subset files to select {num_trials} random trials...")
    try:
        studies = pd.read_csv(os.path.join(AACT_DATA_DIR, 'studies_subset.txt'), sep='|', low_memory=False, on_bad_lines='skip')
        eligibilities = pd.read_csv(os.path.join(AACT_DATA_DIR, 'eligibilities_subset.txt'), sep='|', low_memory=False, on_bad_lines='skip')
        
        relevant_statuses = ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION', 'NOT_YET_RECRUITING']
        active_studies = studies[studies['overall_status'].isin(relevant_statuses)]
        
        if len(active_studies) == 0:
            print("Warning: No active trials found in the subset file to sample from.")
            return None
            
        if len(active_studies) < num_trials:
            num_trials = len(active_studies)
            
        random_sample_df = active_studies.sample(n=num_trials)
        trials_to_analyze_df = pd.merge(random_sample_df, eligibilities, on='nct_id')
        return trials_to_analyze_df

    except FileNotFoundError as e:
        print(f"\nCRITICAL ERROR: {e}\nPlease run 'create_subset.py' first.")
        return None

# --- STEP 3: FEATURE EXTRACTION ---
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

# --- STEP 4: LLM AND MATCHING LOGIC ---
def parse_eligibility_criteria(criteria_text):
    text_to_parse = criteria_text[:8000]
    prompt = f'[INST]Read the following eligibility criteria. Extract key inclusion/exclusion criteria as a JSON object with keys "inclusion" and "exclusion". Do not add explanation. Criteria: "{text_to_parse}"[/INST]'
    outputs = reasoning_pipeline(prompt, max_new_tokens=512, do_sample=False)
    generated_text = outputs[0]['generated_text']
    try:
        json_str = generated_text[generated_text.find('{'):generated_text.rfind('}')+1]
        return json.loads(json_str)
    except json.JSONDecodeError: 
        return {"inclusion": [], "exclusion": []}

def get_embedding(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512).to(model.device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)

# Replace your old scoring function with this new, more robust version

def calculate_match_score(patient_profile, trial_criteria):
    # Start score at 0 and award points for matches.
    score = 0.0
    max_possible_score = 0
    
    patient_full_text = patient_profile.get('text_summary', '')
    if not patient_full_text: return 0.0

    patient_embedding = get_embedding(patient_full_text, embedding_tokenizer, embedding_model)

    # --- Exclusion Criteria Check (Immediate Disqualification) ---
    if trial_criteria.get('exclusion'):
        for criterion in trial_criteria['exclusion']:
            criterion_embedding = get_embedding(criterion, embedding_tokenizer, embedding_model)
            # Use a high similarity threshold for exclusion
            if cosine_similarity(patient_embedding, criterion_embedding).item() > 0.75:
                # If any exclusion criterion is met, the patient is a 0% match.
                return 0.0

    # --- Inclusion Criteria Check (Point-Based Scoring) ---
    if trial_criteria.get('inclusion'):
        # The maximum score is based on the number of inclusion criteria.
        # Let's say each one is worth 20 points.
        max_possible_score = len(trial_criteria['inclusion']) * 20
        if max_possible_score == 0: return 0.0 # Avoid division by zero if no criteria

        for criterion in trial_criteria['inclusion']:
            criterion_embedding = get_embedding(criterion, embedding_tokenizer, embedding_model)
            similarity = cosine_similarity(patient_embedding, criterion_embedding).item()
            
            # If the patient profile and criterion are semantically similar, award points.
            if similarity > 0.6:
                score += 20
    
    if max_possible_score == 0:
        return 0.0

    # Return the score as a percentage of the maximum possible score.
    final_percentage = (score / max_possible_score) * 100
    
    return final_percentage

# --- STEP 5: MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    trials_to_analyze_df = load_random_trials_data(num_trials=NUM_RANDOM_TRIALS)
    if trials_to_analyze_df is None or trials_to_analyze_df.empty:
        print("Could not load random trials to analyze. Exiting.")
        exit()
    
    print("\n--- This Run's Randomly Selected Trials ---")
    for index, trial in trials_to_analyze_df.iterrows():
        print(f"- {trial['nct_id']}: {trial['brief_title']}")
    print("--------------------------------------------\n")

    print("Pre-parsing criteria for selected trials...")
    criteria_cache = {}
    for index, trial in trials_to_analyze_df.iterrows():
        criteria_cache[trial['nct_id']] = parse_eligibility_criteria(trial['criteria'])
    print("Criteria parsing complete.")

    try:
        patient_files = [f for f in os.listdir(SYNTHEA_DATA_DIR) if f.endswith('.json') and not f.startswith(('hospital', 'practitioner'))]
    except FileNotFoundError: patient_files = []
    
    if not patient_files: print("No patient files found.")
    else: print(f"Beginning analysis of {len(patient_files)} patients against {len(trials_to_analyze_df)} random trials...")

    all_successful_matches = []

    for patient_file in tqdm(patient_files, desc="Screening Patients"):
        patient_profile = create_patient_profile(os.path.join(SYNTHEA_DATA_DIR, patient_file))
        if not patient_profile.get('conditions'): continue
        
        for nct_id, parsed_criteria in criteria_cache.items():
            if not parsed_criteria.get('inclusion'): continue
            
            score = calculate_match_score(patient_profile, parsed_criteria)
            
            if score > 65:
                title = trials_to_analyze_df[trials_to_analyze_df['nct_id'] == nct_id]['brief_title'].iloc[0]
                found_patient = next((item for item in all_successful_matches if item["patient_file"] == patient_file), None)
                if found_patient:
                    found_patient['ranked_results'].append({"nct_id": nct_id, "title": title, "score": score})
                else:
                    all_successful_matches.append({
                        "patient_file": patient_file,
                        "conditions": patient_profile.get('conditions', []),
                        "ranked_results": [{"nct_id": nct_id, "title": title, "score": score}]
                    })

    # FINAL SUMMARY
    print("\n\n" + "#"*80)
    print("--- ✅ FINAL SUMMARY: Patients Matched to Randomly Selected Trials ---")
    print("#"*80)
    if not all_successful_matches:
        print("\nNo patients from the cohort were a strong match for this run's random trials.")
    else:
        for match in all_successful_matches:
            match['ranked_results'] = sorted(match['ranked_results'], key=lambda x: x['score'], reverse=True)
        print(f"\nFound {len(all_successful_matches)} patients with potential matches!")
        for match_info in all_successful_matches:
            print(f"\n\n--- Patient: {match_info['patient_file']} ---")
            print(f"    Relevant Conditions: {', '.join(match_info['conditions'][:4])}...")
            print("    --- Matched Trials (Ranked) ---")
            for result in match_info['ranked_results']:
                print(f"      - ({result['score']:.0f}%) {result['nct_id']}: {result['title']}")