import os
import json
import gzip
import re
import readline  # Enables command history and editing
from tqdm import tqdm

# File paths
DATA_FILE = "dict-conjugated.json.gz"
ANNOTATIONS_FILE = "annotated_citations.json"
PROGRESS_FILE = ".annotation_progress"
REQUIRED_TAGS_FILE = ".required_tags"


# Initial setup to collect tag order
def get_tags_in_order():
    tags = []
    print("Set tags in the desired order. Type 'done' when finished.")
    while True:
        tag = input("Enter tag (or 'done' to finish): ").strip()
        if tag.lower() == 'done':
            break
        elif tag:
            tags.append(tag)
    return tags

# Collect tags once in the initial order
if os.path.exists(REQUIRED_TAGS_FILE):
    with open(REQUIRED_TAGS_FILE, "r") as f:
        tag_order = json.load(f)
    print("Loaded tag order from previous session.")
else:
    tag_order = get_tags_in_order()
    with open(REQUIRED_TAGS_FILE, "w") as f:
        json.dump(tag_order, f)
    print("Tag order saved for future use.")

# Main entry function modified to prompt for tags in the defined order

# Load dataset and optionally existing annotations
with gzip.open(DATA_FILE, "rt") as f:
    data = json.load(f)

if os.path.exists(ANNOTATIONS_FILE):
    with open(ANNOTATIONS_FILE, "r", encoding="utf-8") as f:
        annotations = json.load(f)
    print("Loaded existing annotations.")
else:
    annotations = []

# Create a dictionary for quick lookup of annotated entries by definition
annotation_map = {entry['d']: entry for entry in annotations}

# Load progress or start from scratch
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        start_index = int(f.read().strip())
    print(f"Resuming from entry #{start_index}.")
else:
    start_index = 0  # Start from the first entry

used_tags = set()  # Store tags for auto-completion

def setup_readline():
    """Configure readline for command history and auto-completion."""
    readline.parse_and_bind("tab: complete")  # Enable tab completion
    history_file = ".annotation_history"  # Save command history here
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass  # No history file yet

    import atexit
    atexit.register(lambda: readline.write_history_file(history_file))

def get_required_tags():
    """Load or ask for required tags."""
    if os.path.exists(REQUIRED_TAGS_FILE):
        with open(REQUIRED_TAGS_FILE, "r") as f:
            tags = json.load(f)
        print(f"Loaded required tags: {', '.join(tags)}")
    else:
        print("Enter the tags you want to specify for each annotation (comma-separated):")
        tags = input("Required tags: ").strip().split(",")
        tags = [tag.strip() for tag in tags if tag.strip()]
        with open(REQUIRED_TAGS_FILE, "w") as f:
            json.dump(tags, f)
    return tags

def highlight_match(text, pattern):
    """Highlight matching parts of the text using ANSI escape codes."""
    return re.sub(
        pattern, 
        lambda m: f"\033[93m{m.group(0)}\033[0m",  # Highlight in yellow
        text
    )

def suggest(tag_or_value):
    """Suggest tags or values based on previously entered data."""
    suggestions = [item for item in used_tags if item.startswith(tag_or_value)]
    if suggestions:
        print(f"Suggestions: {', '.join(suggestions)}")

def check_required_tags(entry, required_tags):
    """Check if all required tags are present and return any missing ones."""
    missing_tags = [tag for tag in required_tags if tag not in entry['tags']]
    return missing_tags

def annotate_entry(entry, pattern, required_tags):
    """Interactive REPL for annotating a single entry."""
    highlighted_def = highlight_match(entry['d'], pattern)
    print(f"\nDefinition: {highlighted_def}")
    print("Commands: [d]one, [s]kip, [e]dit, [b]ack")

    # Use existing tags if this entry has already been annotated
    if entry['d'] in annotation_map:
        entry = annotation_map[entry['d']]
        print(f"Current Tags: {entry.get('tags', {})}")
    else:
        entry['tags'] = {}  # Initialize tags if not present

    valid_commands = {"d": "done", "s": "skip", "e": "edit", "b": "back"}

    while True:
        tag = input("Enter tag (or command): ").strip()

        # If the input is blank, skip to the next entry.
        if not tag:
            print("Blank input. Skipping to next entry.")
            return "skip"

        # Check if the input is a valid command
        if tag in valid_commands:
            if tag == "d":
                # Check for missing required tags before marking as done
                missing_tags = check_required_tags(entry, required_tags)
                if missing_tags:
                    print(f"Missing required tags: {', '.join(missing_tags)}")
                    print("Please add the missing tags before marking as done.")
                    continue  # Go back to input mode
            return valid_commands[tag]

        # Tag entry
        suggest(tag)  # Provide tag suggestions
        value = input(f"Enter value for tag '{tag}': ").strip()
        if not value:  # Skip empty values
            print("Empty value. Skipping this tag.")
            continue

        suggest(value)  # Provide value suggestions
        entry['tags'][tag] = value
        used_tags.update([tag, value])  # Track used tags and values

    # Update the annotation map with the latest tags
    annotation_map[entry['d']] = entry

def filter_entries(pattern, data):
    """Filter entries based on a regex pattern."""
    regex = re.compile(pattern)
    return [entry for entry in data if regex.search(entry['d'])]

def save_progress(index):
    """Save the current progress index to a file."""
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(index))

# Setup command history and completion
setup_readline()

# Get required tags from the user or load from file
required_tags = get_required_tags()

# Ask the user for a regex pattern to filter entries
pattern = input("Enter regex pattern to filter entries (or press Enter for default): ").strip()
if not pattern:
    pattern = r"([\wÀ-ÖØ-öø-ÿ'()\-\[\]{}\"“”‘’]*?)eme(?=\W|$)"

filtered_data = filter_entries(pattern, data)
print(f"Found {len(filtered_data)} matching entries.")

# REPL Loop: Annotate entries with back navigation support
i = start_index  # Start from the last saved progress
while i < len(filtered_data):
    entry = filtered_data[i]

    result = annotate_entry(entry, pattern, required_tags)
    if result == "done":
        # Save the annotated entry to the annotation map
        annotation_map[entry['d']] = entry
        i += 1  # Move to the next entry
    elif result == "skip":
        i += 1  # Move to the next entry without saving
    elif result == "back":
        if i > 0:
            i -= 1  # Move back to the previous entry
            print(f"Moved back to entry #{i}.")
        else:
            print("Already at the first entry. Can't go back.")

    # Save progress and annotations incrementally
    save_progress(i)
    with open(ANNOTATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(annotation_map.values()), f, ensure_ascii=False, indent=4)

print(f"Annotations saved to {ANNOTATIONS_FILE}.")
print(f"Progress saved. You can resume from where you left off.")


# Function to prompt for tags based on the saved order
def prompt_for_tags_in_order(entry, tag_order):
    tag_values = {}
    print("Please enter values for each tag as per the specified order:")
    for tag in tag_order:
        value = input(f"Enter value for tag '{tag}': ").strip()
        if value:
            tag_values[tag] = value
    entry.update(tag_values)

# Main loop for annotation with ordered tags
for index, entry in enumerate(tqdm(data[start_index:]), start=start_index):
    if entry['d'] in annotation_map:
        continue  # Skip if already annotated

    print(f"Annotating entry: {entry['d']}")
    prompt_for_tags_in_order(entry, tag_order)

    # Save each annotation
    annotations.append(entry)
    with open(ANNOTATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)
