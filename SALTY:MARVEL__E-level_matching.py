#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 13:14:07 2024np.array([0])

@author: physicsstudent
"""

import pandas as pd
import matplotlib.pyplot as plt

no_exact_match_counter = 0   # Global counter for MARVEL rows without an exact match
no_match_within_Erange_counter = 0    #Global counter for MARVEL rows without any possible matches within +/- 50 of energy range
rows_with_perfect_match_counter = 0    #Global counter for MARVEL rows with perfect match (v's, J, K, L3, L4, closest energy)
salty_conflict_counter = 0    #Global counter for SALTY rows which have been matched to multiple MARVEL rows.
marvel_conflict_counter = 0    #Global counter for total number of MARVEL rows involved in a conflict (conflict = more than one marvel row has been matched to one SALTY row)
no_match_within_Erange_list = []  # List to store MARVEL rows with no matches within the energy range
matched_salty_lines = {}    #List to track the matches that have been made to each SALTY line

def match_single_energy(v2_v4tag: str, v1_v3tag: str, Ktag: str, Jtag: str, energy: float, energy_col: int, match_data: pd.DataFrame, v1tag_col: int, v2tag_col: int, v3tag_col: int, v4tag_col: int, Ktag_col: int, Jtag_col: int, Marvel_row: pd.Series) -> pd.DataFrame:
    # Calculate energy differences and filter based on range
    energy_difference = match_data.iloc[:, energy_col].sub(energy).abs()
    filtered_data = match_data[energy_difference <= 20].copy()
    filtered_data['Energy Difference'] = energy_difference[energy_difference <= 50]

    # Filter for J tag
    filtered_data = filtered_data[filtered_data.iloc[:, Jtag_col] == Jtag]
    
    return filtered_data if not filtered_data.empty else None

def combine_rows(Marvel_row: pd.Series, match_data: pd.DataFrame, Marvel_energy_col: int, SALTY_energy_col: int, SALTY_Jtag_col: int, SALTY_Ktag_col: int, SALTY_v1tag_col: int, SALTY_v2tag_col: int, SALTY_v3tag_col: int, SALTY_v4tag_col: int) -> pd.Series:
    global no_exact_match_counter, no_match_within_Erange_counter, rows_with_perfect_match_counter, matched_salty_lines, salty_conflict_counter, marvel_conflict_counter

    # Marvel parameters
    Jtag = Marvel_row[6]
    Ktag = Marvel_row[7]
    v1_v3tag = Marvel_row[0] + Marvel_row[2]
    v2_v4tag = Marvel_row[1] + Marvel_row[3]
    energy = Marvel_row[Marvel_energy_col]

    # Get filtered SALTY data
    filtered_data = match_single_energy(v2_v4tag, v1_v3tag, Ktag, Jtag, energy, SALTY_energy_col, match_data, SALTY_v1tag_col, SALTY_v2tag_col, SALTY_v3tag_col, SALTY_v4tag_col, SALTY_Ktag_col, SALTY_Jtag_col, Marvel_row)


    # If no SALTY rows are within the energy range
    if filtered_data is None:
        no_match_within_Erange_counter += 1
        no_match_within_Erange_list.append(Marvel_row.tolist())  # Add the unmatched MARVEL row to the list

        # Print Marvel row with no possible matches
        print("Marvel row with no possible matches and closest SALTY row with same J:")
        print("v1,v2,v3,v4,  J,  K,L3,L4, energy")
        print(Marvel_row[[0, 1, 2, 3, 6, 7, 8, 9, 14]].tolist())

        # Find the SALTY row with the same J tag and closest energy
        SALTY_same_J = match_data[match_data.iloc[:, SALTY_Jtag_col] == Jtag]
        if not SALTY_same_J.empty:
            SALTY_same_J['Energy Difference'] = SALTY_same_J.iloc[:, SALTY_energy_col].sub(energy).abs()
            closest_SALTY_row = SALTY_same_J.loc[SALTY_same_J['Energy Difference'].idxmin()]
            print(closest_SALTY_row[[9, 10, 11, 12, 3, 6, 1, 'Energy Difference']].tolist())
            print( )
        else:
            print("No SALTY rows with the same J tag found.")
            print( )
        return None
    
    
    if filtered_data is not None:
        # Define the columns to compare
        Marvel_criteria = [Marvel_row[i] for i in [0, 1, 2, 3, 6, 7]]
        SALTY_criteria = filtered_data[[9, 10, 11, 12, 3, 6]].values.tolist()

        # Check for exact matches and find the one with the smallest energy difference
        exact_matches = []
        for index, row in enumerate(SALTY_criteria):
            if Marvel_criteria == row:
                energy_diff = abs(energy - filtered_data.iloc[index][SALTY_energy_col])
                exact_matches.append((filtered_data.iloc[index], energy_diff))

        # If exact matches were found, choose the one with the smallest energy difference
        if exact_matches:
            closest_row, smallest_diff = min(exact_matches, key=lambda x: x[1])
            closest_row['Energy Difference'] = smallest_diff
            rows_with_perfect_match_counter += 1
            
            
            # Track the SALTY line being matched
            salty_index = closest_row.name  # Get the index of the matched SALTY row
            if salty_index not in matched_salty_lines:
                matched_salty_lines[salty_index] = [Marvel_row.tolist()]
            else:
                matched_salty_lines[salty_index].append(Marvel_row.tolist())
                
                # Increment the counters for conflicts
                if len(matched_salty_lines[salty_index]) == 2:  # Only count SALTY line once on first conflict
                    salty_conflict_counter += 1
               
                # Count every MARVEL line beyond the first one for this SALTY line
                marvel_conflict_counter += len(matched_salty_lines[salty_index])
                
                # Print conflict details
                print(f"\nConflict detected: Multiple MARVEL lines matched to SALTY index {salty_index}")
                print(f"SALTY line involved: {closest_row.tolist()}")
                
                # Print all MARVEL lines involved in the conflict
                for idx, marvel in enumerate(matched_salty_lines[salty_index]):
                    print(f"\nMARVEL line {idx + 1}: {marvel}")
                    
                    # Find all possible SALTY matches for this MARVEL line
                    possible_salty_matches = match_data[
                        (match_data.iloc[:, SALTY_v1tag_col] == marvel[0]) &
                        (match_data.iloc[:, SALTY_v2tag_col] == marvel[1]) &
                        (match_data.iloc[:, SALTY_v3tag_col] == marvel[2]) &
                        (match_data.iloc[:, SALTY_v4tag_col] == marvel[3]) &
                        (match_data.iloc[:, SALTY_Jtag_col] == marvel[6]) &
                        (match_data.iloc[:, SALTY_Ktag_col] == marvel[7])
                    ]
                    print(f"Possible SALTY matches for MARVEL line {idx + 1}:")
                    print(possible_salty_matches[[0, 9, 10, 11, 12, 3, 6, 13, 14, 1]].to_string(index=False))
                
                print("\n")

            return pd.concat([Marvel_row, closest_row])

        # If no exact match, calculate energy difference and sort by it
        no_exact_match_counter += 1
        filtered_data['Energy Difference'] = filtered_data[SALTY_energy_col].apply(lambda x: abs(energy - x))
        sorted_filtered_data = filtered_data.sort_values(by='Energy Difference', ascending=True)

        # Print the Marvel row currently being matched (only specified columns)
        print("Marvel row:")
        print("v1,v2,v3,v4,  J,  K,L3,L4, energy")
        print(Marvel_row[[0, 1, 2, 3, 6, 7, 8, 9, 14]].tolist())

        # Print filtered data in order of energy difference
        print("No exact match; displaying possible matches:")
        print(sorted_filtered_data[[9, 10, 11, 12, 3, 6, 13, 14, 1, 'Energy Difference']].to_string(index=False, header=False))

    return None

def main() -> None:
    global no_exact_match_counter, no_match_within_Erange_counter

    data_path = "/Users/physicsstudent/Desktop/Phosphine/Match_trials/"
    Marvel_filename = "trial_04/MARVEL_Energies(E)_12_4_2025_0_53.txt.txt"
    SALTY_filename = "31P-1H3__SAlTY_E.txt"
    out_filename = "trial_04/Matched_Energies(E)_Output_20_04.txt"
    
    Marvel_energy_col = 14  # Use the 15th column for Marvel energies
    SALTY_energy_col = 1    # Use the 2nd column for SALTY energies
    SALTY_Jtag_col = 3      # Use the 4th column in SALTY for matching tags
    SALTY_Ktag_col = 6      # Use the 7th column in SALTY for matching tags
    SALTY_v1tag_col= 9      # Use the 10th column in SALTY for matching tags
    SALTY_v2tag_col= 10     # Use the 11th column in SALTY for matching tags
    SALTY_v3tag_col= 11     # Use the 12th column in SALTY for matching tags
    SALTY_v4tag_col= 12     # Use the 13th column in SALTY for matching tags

    magic_number = 8.371

    print("Loading data")
    # Load the data without setting an index
    Marvel_data = pd.read_csv(data_path + Marvel_filename, delim_whitespace=True, header=None)
    SALTY_data = pd.read_csv(data_path + SALTY_filename, delim_whitespace=True, header=None)
    
    # Apply the magic number to the energy column of the Marvel data
    Marvel_data[Marvel_energy_col] += magic_number
    
    print("Matching data")
    # Apply the `combine_rows` function row-by-row to Marvel_data
    out_df = Marvel_data.apply(lambda x: combine_rows(x, SALTY_data, Marvel_energy_col, SALTY_energy_col, SALTY_Jtag_col, SALTY_Ktag_col, SALTY_v1tag_col, SALTY_v2tag_col, SALTY_v3tag_col, SALTY_v4tag_col), axis=1)
    
    # Print the total count of MARVEL rows without an exact match
    print(f"Total number of MARVEL rows without an exact match: {no_exact_match_counter}")
    
    # Print the total number of MARVEL rows that has no possible matches in filtered data
    print(f"Total number of MARVEL rows without any candidates within the filtering requirements: {no_match_within_Erange_counter }")
    
    # Print the total number of MARVEL rows with a perfect match
    print(f"Total number of MARVEL rows with perfect match: {rows_with_perfect_match_counter}")
    
    # Print conflict counters
    print(f"Total SALTY lines involved in conflicts: {salty_conflict_counter}")
    print(f"Total MARVEL lines involved in conflicts: {marvel_conflict_counter}")
    
    # Extract energy differences of perfect matches
    if not out_df.dropna().empty:
        energy_diff_col_index = out_df.shape[1] - 1  # Last column is assumed to be "Energy Difference"
        energy_differences = out_df.dropna().iloc[:, energy_diff_col_index]

        # Plot histogram
        plt.figure(figsize=(8, 5))
        plt.hist(energy_differences, bins=15, color='blue', edgecolor='black', alpha=0.7)
        plt.xlabel('Energy Difference (cm^-1)')
        plt.ylabel('Number of Matches within Energy Difference')
        plt.title('Distribution of Energy Differences for Perfect Matches of E-levels')
        plt.grid(True)
        plt.show()
    
    # Compute the average energy difference if perfect match exist
    if not out_df.dropna().empty:
        energy_diff_col_index = out_df.shape[1] - 1  # Last column assumed to be "Energy Difference"
        avg_energy_diff = out_df.dropna().iloc[:, energy_diff_col_index].mean()
        print(f"Average Energy Difference of perfect matches: {avg_energy_diff}")

    print("Example of matched energies:")
    if out_df is not None:
        print(out_df.head())  # Print the first few rows for verification
    
    # Save the resulting DataFrame to a file, excluding rows where no match was found
    out_df.dropna().to_csv(data_path + out_filename, sep=' ', header=False, index=False)
    
    # Save unmatched MARVEL rows to a separate file
    if no_match_within_Erange_list:
        unmatched_df = pd.DataFrame(no_match_within_Erange_list)
        unmatched_filename = data_path + "no_match_within_Erange.txt"
        unmatched_df.to_csv(unmatched_filename, sep=' ', header=False, index=False)
        print(f"Unmatched MARVEL rows saved to {unmatched_filename}")

# Run the main function if the script is executed
if __name__ == "__main__":
    main()
