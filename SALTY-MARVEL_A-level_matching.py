"""

This script is used to match A-levels between MARVEL and SALTY datasets for phosphine molecules using a set of quantum numbers (v1, v2, v3, v4, J, K, L3, L4, L, sum_tot). It filters candidate matches based on quantum numbers and energy proximity, selects the closest matches, and flags cases with large energy differences or multiple matches (conflicts). It outputs matched entries into a file, reports unmatched or problematic cases, calculates the average energy difference between matched pairs, and visualizes the distribution of these differences with a histogram.

"""

import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

# File paths
marvel_path = 'Output_MARVEL_A-levels.txt'
salty_path = 'Original_SALTY_A-energy_states.txt' 
output_path = marvel_path.rsplit('/', 1)[0] + '/MARVEL-SALTY_matched_A-levels.txt'

# Load MARVEL data
marvel_columns = ['v1', 'v2', 'v3', 'v4', 'l3', 'l4', 'J', 'K', 'L3', 'L4', 'L', 'sym_rot', 'sym_vib', 'sym_tot', 'energy', 'uncertainty', 'num_transitions']
marvel_data = pd.read_csv(marvel_path, delim_whitespace=True, names=marvel_columns)

# Load SALTY data
salty_columns = ['line_number', 'frequency', 'gtot', 'J', 'uncertainties', 'sym_tot', 'K', 'sym_rot', 'L', 'v1', 'v2', 'v3', 'v4', 'L3', 'L4', 'sym_vib'] + [f'col_{i}' for i in range(17, 24)]
salty_data = pd.read_csv(salty_path, delim_whitespace=True, names=salty_columns)

# Dictionary to track conflicts
conflicts = defaultdict(list)

# Matching process
matches = {}
unmatched = []
energy_differences = []
matched_rows = []

for index, marvel_row in marvel_data.iterrows():
    filtered_salty = salty_data[(salty_data['J'] == marvel_row['J']) &
                                (abs(salty_data['frequency'] - marvel_row['energy']) <= 100)]
    
    filtered_salty = filtered_salty[(filtered_salty['v1'] == marvel_row['v1']) &
                                     (filtered_salty['v2'] == marvel_row['v2']) &
                                     (filtered_salty['v3'] == marvel_row['v3']) &
                                     (filtered_salty['v4'] == marvel_row['v4']) &
                                     (filtered_salty['K'] == marvel_row['K']) &
                                     (filtered_salty['L3'] == marvel_row['L3']) &
                                     (filtered_salty['L4'] == marvel_row['L4']) &
                                     (filtered_salty['L'] == marvel_row['L']) &
                                     (filtered_salty['sym_tot'] == marvel_row['sym_tot'])]
    
    if not filtered_salty.empty:
        closest_match = filtered_salty.iloc[(filtered_salty['frequency'] - marvel_row['energy']).abs().argsort()[:1]]
        salty_index = closest_match.index[0]
        energy_difference = abs(closest_match['frequency'].values[0] - marvel_row['energy'])
        energy_differences.append(energy_difference)

        if energy_difference > 20:
            print(f'Large energy difference detected: {energy_difference:.2f}')
            print(f'MARVEL line (index {index}): {marvel_row.tolist()}')
            print(f'SALTY match (index {salty_index}): {closest_match.iloc[0].tolist()}')
            print('\n')
        
        matches.setdefault(salty_index, []).append(index)
        
        if len(matches[salty_index]) > 1:
            conflicts[salty_index] = matches[salty_index]
        
        matched_rows.append(marvel_row.tolist() + closest_match.iloc[0].tolist())
    else:
        unmatched.append(index)
        print(f'No match found for MARVEL row {index}. Listing SALTY candidates:')
        print(f'MARVEL row: {marvel_row.tolist()}')
        nearby_salty = salty_data[(salty_data['J'] == marvel_row['J']) &
                                  (abs(salty_data['frequency'] - marvel_row['energy']) <= 50)]
        print(nearby_salty[['line_number', 'v1', 'v2', 'v3', 'v4', 'J', 'K', 'L3', 'L4', 'L', 'sym_tot', 'frequency']])
        print('\n')

# Handle conflicts
for salty_index, marvel_indices in conflicts.items():
    salty_row = salty_data.loc[salty_index, ['line_number', 'v1', 'v2', 'v3', 'v4', 'J', 'K', 'L3', 'L4', 'L', 'sym_tot', 'frequency']]
    print(f'Conflict detected: Multiple MARVEL lines matched to SALTY index {salty_index}')
    print(f'SALTY line involved: {salty_row.tolist()}')
    
    for marvel_index in marvel_indices:
        marvel_row = marvel_data.loc[marvel_index]
        print(f'MARVEL line: {marvel_row.tolist()}')
        possible_salty_matches = salty_data[(salty_data['J'] == marvel_row['J']) &
                                            (salty_data['v1'] == marvel_row['v1']) &
                                            (salty_data['v2'] == marvel_row['v2']) &
                                            (salty_data['v3'] == marvel_row['v3']) &
                                            (salty_data['v4'] == marvel_row['v4']) &
                                            (salty_data['K'] == marvel_row['K']) &
                                            (salty_data['L3'] == marvel_row['L3']) &
                                            (salty_data['L4'] == marvel_row['L4']) &
                                            (salty_data['L'] == marvel_row['L']) &
                                            (salty_data['sym_tot'] == marvel_row['sym_tot'])]
        print(f'Possible SALTY matches for MARVEL line:')
        print(possible_salty_matches[['line_number', 'v1', 'v2', 'v3', 'v4', 'J', 'K', 'L3', 'L4', 'L', 'sym_tot', 'frequency']])
        print('\n')

# Write matched rows to file
with open(output_path, 'w') as f:
    for row in matched_rows:
        f.write(' '.join(map(str, row)) + '\n')
        
# Print average energy difference
if energy_differences:
    average_diff = np.mean(energy_differences)
    print(f'Average energy difference: {average_diff:.4f}')
else:
    print('No energy differences to compute average.')
    

# Summary of conflicts
print(f'Total conflicts found: {sum(len(v) for v in conflicts.values())}')


# Plot histogram
plt.figure(figsize=(8, 5))
plt.hist(energy_differences, bins=100, color='blue', edgecolor='black', alpha=0.7)
plt.xlabel('Energy Difference (cm^-1)')
plt.ylabel('Number of Matches within Energy Difference')
plt.title('Distribution of Energy Differences for Perfect Matches of A-levels')
plt.grid(True)
plt.show()

    
