import json, re
from collections import Counter
import pandas as pd

# Load and preprocess data
data = json.load(open('annotated_citations.json'))
extract = lambda c: ", ".join(re.search(r'\(([^)]+)\)', c).group(1).split(", ")[:2]) if re.search(r'\(([^)]+)\)', c) else None

# Initialize variables
ds_count = ss_count = 0
seen_citations = set()
source_counts, ss_counts = Counter(), Counter()

# Process data in a single loop
for e in data:
    tags, cit, sujs, sujp = e.get('tags', {}), e.get('tags', {}).get('cit'), e.get('tags', {}).get('sujs'), e.get('tags', {}).get('sujp')
    if cit and cit not in seen_citations:
        seen_citations.add(cit)  # Track unique citations
        src = extract(cit)
        if src:
            source_counts[src] += 1  # Count source
            ss_counts[src] += (sujs == sujp)  # Count SS cases
            if sujs and sujp:
                if sujs == sujp:
                    ss_count += 1  # Increment SS count
                else:
                    ds_count += 1  # Increment DS count

# Calculate frequencies
total_entries_no_duplicates = len(seen_citations)
ss_frequency = ss_count / total_entries_no_duplicates * 100 if total_entries_no_duplicates > 0 else 0
ds_frequency = ds_count / total_entries_no_duplicates * 100 if total_entries_no_duplicates > 0 else 0

# Results
final_results = {
    "Total Entries (No Duplicates)": total_entries_no_duplicates,
    "SS Count": ss_count,
    "SS Frequency (%)": round(ss_frequency, 2),
    "DS Count": ds_count,
    "DS Frequency (%)": round(ds_frequency, 2),
    "Conjunctive as DS Marker": "Yes" if ds_frequency > ss_frequency else "No",
    "Conjunctive in SS Situation Permissible": "Yes" if ss_count > 0 else "No"
}

# Prepare DataFrame for source analysis
df = pd.DataFrame([{"Source": s, "Annotation Count": c, "SS Annotation Count": ss_counts[s]} for s, c in source_counts.items()])

# Display results
print(df)


def generate_latex_macros(results):
    """
    Generates LaTeX macro definitions for analysis results.

    Parameters:
    - results (dict): The analysis results dictionary containing SS and DS statistics.

    Returns:
    - str: LaTeX-friendly macro definitions as a string.
    """
    latex_macros = [
        f"\\newcommand{{\\totalN}}{{{results['Total Entries (No Duplicates)']}}}",
        f"\\newcommand{{\\ssCount}}{{{results['SS Count']}}}",
        f"\\newcommand{{\\ssFrequency}}{{{results['SS Frequency (%)']:.2f}}}",
        f"\\newcommand{{\\dsCount}}{{{results['DS Count']}}}",
        f"\\newcommand{{\\dsFrequency}}{{{results['DS Frequency (%)']:.2f}}}",
        f"\\newcommand{{\\conjunctiveDS}}{{{results['Conjunctive as DS Marker']}}}",
        f"\\newcommand{{\\conjunctiveSS}}{{{results['Conjunctive in SS Situation Permissible']}}}"
    ]
    return "\n".join(latex_macros)

def print_results_latex_with_macros(results):
    """
    Prints analysis results in a LaTeX-friendly format using macros.

    Parameters:
    - results (dict): The analysis results dictionary containing SS and DS statistics.
    """
    latex_macros = generate_latex_macros(results)
    
    latex_table = f"""
% Macro definitions
{latex_macros}

\\begin{{table}}[h!]
\\centering
\\begin{{tabular}}{{|l|l|}}
\\hline
\\textbf{{Metric}} & \\textbf{{Value}} \\\\
\\hline
Total Entries & \\totalN \\\\
SS Count & \\ssCount \\\\
SS Frequency (\\%) & \\ssFrequency \\\\
DS Count & \\dsCount \\\\
DS Frequency (\\%) & \\dsFrequency \\\\
Conjunctive as DS Marker & \\conjunctiveDS \\\\
Conjunctive in SS Situation Permissible & \\conjunctiveSS \\\\
\\hline
\\end{{tabular}}
\\caption{{Linguistic analysis of conjunctive environments in Old Tupi.}}
\\label{{tab:conjunctive_analysis}}
\\end{{table}}
"""
    print(latex_table)

# Example usage:
print_results_latex_with_macros(final_results)

def create_latex_table_from_df(df, caption, label):
    """
    Generates a LaTeX table from a DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame to convert to a LaTeX table.
    - caption (str): The caption for the table.
    - label (str): The label for the table.

    Returns:
    - str: LaTeX table as a string.
    """
    latex_rows = []
    for _, row in df.iterrows():
        latex_rows.append(f"{row['Source']} & {row['Annotation Count']-row['SS Annotation Count']} & {row['SS Annotation Count']} \\\\")
    
    latex_table = f"""
\\begin{{table}}[h!]
\\centering
\\begin{{tabular}}{{|l|c|c|}}
\\hline
\\textbf{{Source}} & \\textbf{{DS Annotation Count}} & \\textbf{{SS Annotation Count}} \\\\
\\hline
{chr(10).join(latex_rows)}
\\hline
\\end{{tabular}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{table}}
"""
    return latex_table

# Example usage
latex_table = create_latex_table_from_df(
    df,
    caption="Annotation counts and SS counts per source.",
    label="tab:annotation_counts"
)
print(latex_table)
