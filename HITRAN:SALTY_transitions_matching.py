#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 11:25:23 2025

@author: physicsstudent
"""

import re

def load_states(states_file):
    states_dict = {}
    with open(states_file, 'r') as f:
        for line in f:
            cols = re.split(r'\s+', line.strip())
            if len(cols) >= 14:
                ref = cols[0]
                v1 = str(int(float(cols[9])))
                v2 = str(int(float(cols[10])))
                v3 = str(int(float(cols[11])))
                v4 = str(int(float(cols[12])))
                J  = str(int(float(cols[3])))
                K  = str(int(float(cols[6])))
                g  = str(int(float(cols[2])))
                states_dict[ref] = (v1, v2, v3, v4, J, K, g)
    return states_dict

def extract_hitran_qnums(columns, upper=True):
    """Extract quantum numbers from HITRAN line columns."""
    if upper:
        indices = [5, 6, 7, 8, 13, 14, 26]
    else:
        indices = [9, 10, 11, 12, 16, 17, 27]
    return tuple(str(int(float(columns[i]))) for i in indices)

def main():
    hitran_file = "/Users/physicsstudent/Desktop/Phosphine/plotting/spectra_graph/chosen_hitran_trans_E.txt"
    salty_trans_file = "/Users/physicsstudent/Desktop/Phosphine/plotting/spectra_graph/SAlTY_transition_files/31P-1H3__SAlTY__04300-04400.trans"
    salty_states_file = "/Users/physicsstudent/Desktop/Phosphine/Match_trials/31P-1H3__SAlTY_E.txt"
    
    output_file = "/Users/physicsstudent/Desktop/Phosphine/plotting/spectra_graph/matched_transitions_E.txt"
    hitran_output_file = "/Users/physicsstudent/Desktop/Phosphine/plotting/spectra_graph/hitran_with_matches_E.txt"

    print("Loading SALTY states...")
    states = load_states(salty_states_file)

    print("Indexing SALTY transitions...")
    salty_dict = {}
    salty_energies = {}  # Store transition energies for fast lookup
    with open(salty_trans_file, 'r') as f:
        for line in f:
            cols = re.split(r'\s+', line.strip())
            if len(cols) >= 3:  # energy should be in 3rd column
                upper_ref, lower_ref, trans_E = cols[0], cols[1], float(cols[2])
                if upper_ref in states and lower_ref in states:
                    key = (states[upper_ref], states[lower_ref])
                    salty_dict.setdefault(key, []).append(line.strip())
                    salty_energies[(upper_ref, lower_ref)] = trans_E

    print("Matching transitions...")
    match_count = 0
    candidates = []

    with open(hitran_file, 'r') as hitran:
        for linenum, line in enumerate(hitran, 1):
            cols = re.split(r'\s+', line.strip())
            if len(cols) >= 28:
                upper_qnums = extract_hitran_qnums(cols, upper=True)
                lower_qnums = extract_hitran_qnums(cols, upper=False)
                hitran_E = float(cols[1])  # HITRAN transition energy

                matches = salty_dict.get((upper_qnums, lower_qnums))
                if matches:
                    for match_line in matches:
                        parts = re.split(r'\s+', match_line)
                        upper_ref, lower_ref = parts[0], parts[1]
                        salty_E = salty_energies.get((upper_ref, lower_ref), None)
                        if salty_E is not None:
                            diff = abs(hitran_E - salty_E)
                            ref_tag = f"{upper_ref}_{lower_ref}"
                            candidates.append((linenum, line.strip(), ref_tag, match_line, diff))
                else:
                    print(f"[No Match - Line {linenum}] upper: {upper_qnums}, lower: {lower_qnums}")

    print("Selecting best matches...")

    # Step 1: Keep best SALTY match per HITRAN transition
    best_per_hitran = {}
    for linenum, hitran_line, ref_tag, salty_line, diff in candidates:
        if linenum not in best_per_hitran or diff < best_per_hitran[linenum][3]:
            best_per_hitran[linenum] = (hitran_line, ref_tag, salty_line, diff)

    # Step 2: Resolve conflicts where multiple HITRAN transitions map to the same SALTY
    salty_to_best_hitran = {}
    for linenum, (hitran_line, ref_tag, salty_line, diff) in best_per_hitran.items():
        if ref_tag not in salty_to_best_hitran or diff < salty_to_best_hitran[ref_tag][3]:
            salty_to_best_hitran[ref_tag] = (linenum, hitran_line, salty_line, diff)

    print("Writing final matches...")
    with open(output_file, 'a') as out, open(hitran_output_file, 'a') as hitran_out:
        for ref_tag, (linenum, hitran_line, salty_line, diff) in salty_to_best_hitran.items():
            out.write(salty_line + "\n")
            hitran_out.write(hitran_line + "\t" + ref_tag + "\n")
            match_count += 1

    print(f"\nTotal final matches: {match_count}")
    print(f"Wrote HITRAN matches to: {hitran_output_file}")
    print(f"Wrote SALTY matches to: {output_file}")

if __name__ == "__main__":
    main()
