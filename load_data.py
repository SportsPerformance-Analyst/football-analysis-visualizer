import os
import json
import pandas as pd
import matplotlib
from mplsoccer import Pitch
import tkinter as tk
import matplotlib.pyplot as plt
from tkinter import simpledialog, messagebox
matplotlib.use('TkAgg')
import argparse

# colletct argomans from GUI or Command Line
parser = argparse.ArgumentParser(description="Football xG Analysis Tool")
parser.add_argument('--save_path', type=str, help='Path to save output files')
parser.add_argument('--match_id', type=int, help='Match ID selected from GUI')
args = parser.parse_args()

external_save_path = args.save_path
external_match_id = args.match_id


# Find base directory of the project (where "data" folder is located)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')

# Build exact path to the JSON files
events_path = os.path.join(data_dir, 'sb_events.json')
matches_path = os.path.join(data_dir, 'sb_matches.json')

# Check file existence
if not os.path.exists(events_path):
    raise FileNotFoundError(f"sb_events.json file not found at: {events_path}")
    if not os.path.exists(matches_path):
        raise FileNotFoundError(f"sb_matches.json file not found at: {matches_path}")

# Load JSON files
with open(events_path, encoding='utf-8') as f:
    event_data = json.load(f)

with open(matches_path, encoding='utf-8') as f:
    match_data = json.load(f)

# Convert JSON to DataFrame
events_df = pd.json_normalize(event_data)
matches_df = pd.json_normalize(match_data)

# Initial display for verification
print("Sample Events Data:")
print(events_df.head())

print("\nMatch Information:")
print(matches_df[['home_team.home_team_name', 'away_team.away_team_name', 'competition.competition_name']].head())

# Display match info to find match_id
print("Available Matches:")
print(matches_df[['match_id', 'home_team.home_team_name', 'away_team.away_team_name']])

# GUI to get match_id
def get_match_id(matches_df):
    import tkinter as tk
    from tkinter import simpledialog, messagebox

    # Inner function to get input after displaying list
    def submit():
        match_id_input = simpledialog.askstring("Enter Match ID", "Enter the desired match_id:")
        root.match_id_input = match_id_input
        root.destroy()

    # Main Window
    root = tk.Tk()
    root.title("Match List")
    root.geometry("800x600")

    # Textual Window- Scrollbar
    text_box = tk.Text(root, wrap=tk.WORD, font=("Consolas", 10))
    scrollbar = tk.Scrollbar(root, command=text_box.yview)
    text_box.configure(yscrollcommand=scrollbar.set)

    text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Writing list of Matches in Text box
    for _, row in matches_df.iterrows():
        line = f"{row['match_id']}: {row['home_team.home_team_name']} vs {row['away_team.away_team_name']}\n"
        text_box.insert(tk.END, line)

    # Match Id Bottom
    submit_btn = tk.Button(root, text="Enter match_id", command=submit)
    submit_btn.pack(pady=10)

    # Loop MAin Window Running
    root.mainloop()
    return root.match_id_input

#
if external_match_id is not None:
    match_id = int(external_match_id)
else:
    match_id_input = get_match_id(matches_df)

    if not match_id_input:
        messagebox.showwarning("Cancelled", "No ID entered. Program terminated.")
        exit()

    match_id = int(match_id_input)


filtered_events = events_df[events_df['match_id'] == match_id]

# Filter only shot events
shots = filtered_events[filtered_events['type.name'] == 'Shot'].copy()

# Remove rows without location or xG
shots = shots[shots['location'].notna() & shots['shot.statsbomb_xg'].notna()]

# Check if any valid shots exist
if shots.empty:
    print("❌ No valid shot events (with location and xG) found for this match.")
    exit()

# Find match info from matches_df
match_row = matches_df[matches_df['match_id'] == match_id].iloc[0]

# Get team names and match date
home_team = match_row['home_team.home_team_name'].replace(" ", "_")
away_team = match_row['away_team.away_team_name'].replace(" ", "_")
match_date = match_row['match_date']  # sample format 2021-10-15
team_a = shots['team.name'].unique()[0]
team_b = shots['team.name'].unique()[1]


# Calculate match result and display goal scorers

goals = filtered_events[
    (filtered_events['type.name'] == 'Shot') &
    (filtered_events['shot.outcome.name'] == 'Goal')
].copy()

# gaols time
goals['goal_minute'] = goals['minute'] + goals['second'] / 60


# Goals per team
goals_by_team = goals['team.name'].value_counts()
print("\nMatch Result:")
for team in [team_a, team_b]:
    print(f"{team}: {goals_by_team.get(team, 0)} goals")

# Goal scorers per team
print("\nGoal Scorers:")
for team in [team_a, team_b]:
    team_goals = goals[goals['team.name'] == team]
    scorers = team_goals['player.name'].value_counts()
    if not scorers.empty:
        print(f"\n{team}:")
        for player, count in scorers.items():
            print(f"  - {player}: {count} Goal")
    else:
        print(f"\n{team}No Goals")

# data
team_a_goals = goals[goals['team.name'] == team_a]
team_b_goals = goals[goals['team.name'] == team_b]

plt.figure(figsize=(12, 4))
plt.title("⏱ Goal Timings by Team", fontsize=14)

# chartings teams goals
plt.scatter(team_a_goals['goal_minute'], [1]*len(team_a_goals), color='green', label=team_a, s=100)
plt.scatter(team_b_goals['goal_minute'], [0]*len(team_b_goals), color='blue', label=team_b, s=100)

# labels
plt.yticks([0, 1], [team_b, team_a])
plt.xlabel("Match Minute")
plt.grid(True, axis='x', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()


# Construct file name
filename = f"{match_date}_{home_team}_vs_{away_team}.csv"

if external_save_path:
    save_dir = external_save_path
else:
    while True:
        save_dir = simpledialog.askstring("Save Path", "Enter the folder path to save the file:")

        if not save_dir:
            messagebox.showwarning("Cancelled", "No path entered. Saving aborted.")
            exit()

        save_dir = save_dir.strip('"').strip("'").strip()

        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            break
        except Exception as e:
            messagebox.showerror("Path Error", f"The entered path is invalid or cannot be created:\n{e}")


# Construct final CSV file path
file_path = os.path.join(save_dir, filename)


# Save CSV to specified path
try:
    filtered_events.to_csv(file_path, index=False, encoding='utf-8-sig')
    messagebox.showinfo("✅ Saved", f"File successfully saved at:\n{file_path}")
    print(f"📁 File saved: {file_path}")
except Exception as e:
    messagebox.showerror("❌ Save Error", str(e))

# XG results
# Filter shots
# Remove invalid xG or location
shots = filtered_events[filtered_events['type.name'] == 'Shot'].copy()
shots = shots[shots['shot.statsbomb_xg'].notna() & shots['location'].notna()]

# xG by team
xg_by_team = shots.groupby('team.name')['shot.statsbomb_xg'].sum()
print("\nTeam xG:")
print(xg_by_team)

# xG by player
xg_by_player = shots.groupby('player.name')['shot.statsbomb_xg'].sum().sort_values(ascending=False)
print("\nTop xG Players:")
print(xg_by_player.head(5))

# calculating xG for each team
team_xg = shots.groupby('team.name')['shot.statsbomb_xg'].sum()
team_goals = goals['team.name'].value_counts()

summary_df = pd.DataFrame({
    'xG': team_xg,
    'Goals': team_goals
}).fillna(0)

summary_df['xG Diff'] = summary_df['Goals'] - summary_df['xG']

# charts in one subplot
fig, axs = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("📊 Team Performance Analysis: xG vs Goals", fontsize=14)

# ===== First chart: xG and goal =====
summary_df[['xG', 'Goals']].plot(kind='bar', ax=axs[0], rot=45)
axs[0].set_title("xG vs Goals")
axs[0].set_ylabel("Count")

# add numerical value on top of charts
for i, (team, row) in enumerate(summary_df.iterrows()):
    axs[0].text(i - 0.2, row['xG'] + 0.1, f"{row['xG']:.2f}", ha='center', color='black', fontsize=9)
    axs[0].text(i + 0.2, row['Goals'] + 0.1, f"{int(row['Goals'])}", ha='center', color='black', fontsize=9)

# ===== second chart: Over/Under Performance =====
colors = summary_df['xG Diff'].apply(lambda x: 'green' if x > 0 else 'red')
summary_df['xG Diff'].plot(kind='bar', ax=axs[1], color=colors, rot=45)
axs[1].axhline(0, linestyle='--', color='gray')
axs[1].set_title("Over/Underperformance\n(Goals - xG)")
axs[1].set_ylabel("Difference")

# numbers on second chart
for i, value in enumerate(summary_df['xG Diff']):
    axs[1].text(x=i, y=value + (0.1 if value > 0 else -0.3), s=f"{value:+.2f}", ha='center', color='black')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])


# Teams
team_a = shots['team.name'].unique()[0]
team_b = shots['team.name'].unique()[1]

# Split halves
shots_first_half = shots[shots['period'] == 1]
shots_second_half = shots[shots['period'] == 2]

# Professional xG map with correct team orientation

pitch = Pitch(pitch_type='statsbomb', line_color='black', pitch_color='white')
# Two Pitches beside Together
fig, axs = pitch.draw(nrows=1, ncols=2, figsize=(18, 9))

# Half titles above pitches
axs[0].set_title("First Half", fontsize=14)
axs[1].set_title("Second Half", fontsize=14)

# Assumption: Team A attacks left in first half
team_a_attacks_left_first_half = True

# Function to check if shot is in opponent half
def is_in_opponent_half(x, team_name, is_first_half):
    """
    Returns True if shot is in opponent half based on team and match half.
    """
    if team_name == team_a:
        return x > 60 if is_first_half else x < 60
    elif team_name == team_b:
        return x < 60 if is_first_half else x > 60
    return False
def plot_half(ax, data, is_first_half, flip_team_a=False, flip_team_b=False):
    for _, row in data.iterrows():
        loc = row.get('location')
        if isinstance(loc, list) and len(loc) >= 2:
            x, y = loc[0], loc[1]
            team = row['team.name']
            xg = row['shot.statsbomb_xg']
            outcome = row['shot.outcome.name']
            player = row.get('player.name', 'Unknown')
            is_goal = outcome == 'Goal'
            color = 'green' if is_goal else 'red'

            # Flip the pitch if necessary
            flip = (team == team_a and flip_team_a) or (team == team_b and flip_team_b)
            if flip:
                x, y = 120 - x, 80 - y

                # Function to check if shot is in opponent half
            if is_in_opponent_half(x, team, is_first_half):
                ax.scatter(x, y, s=xg * 1000, color=color, edgecolors='black', alpha=0.6)
                ax.text(x, y - 2, player, fontsize=6, ha='center', va='top', color='black')


plot_half(axs[0], shots_first_half, is_first_half=True,
          flip_team_a=not team_a_attacks_left_first_half,
          flip_team_b=team_a_attacks_left_first_half)
#Draw First and Second HAlf with Correct Direction
plot_half(axs[1], shots_second_half, is_first_half=False,
          flip_team_a=team_a_attacks_left_first_half,
          flip_team_b=not team_a_attacks_left_first_half)


# Draw team names behind goals
axs[0].text(5, 40, team_a, va='center', ha='center', fontsize=12, rotation=90)
axs[0].text(115, 40, team_b, va='center', ha='center', fontsize=12, rotation=90)
axs[1].text(5, 40, team_b, va='center', ha='center', fontsize=12, rotation=90)
axs[1].text(115, 40, team_a, va='center', ha='center', fontsize=12, rotation=90)

# Draw xG table for each team's players
fig_tables, axs_tables = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
fig_tables.suptitle('xG by Player - Each Team', fontsize=14)

# Breakdown Teams A & B
xg_team_a = shots[shots['team.name'] == team_a].groupby('player.name')['shot.statsbomb_xg'].sum().sort_values(ascending=False).head(10)
xg_team_b = shots[shots['team.name'] == team_b].groupby('player.name')['shot.statsbomb_xg'].sum().sort_values(ascending=False).head(10)

# Team A Table
table_data_1 = [[player, f"{xg:.2f}"] for player, xg in xg_team_a.items()]
axs_tables[0].axis('off')
axs_tables[0].table(cellText=table_data_1, colLabels=['Player', 'xG'], loc='center')
axs_tables[0].set_title(team_a)

# Team B Table
table_data_2 = [[player, f"{xg:.2f}"] for player, xg in xg_team_b.items()]
axs_tables[1].axis('off')
axs_tables[1].table(cellText=table_data_2, colLabels=['Player', 'xG'], loc='center')
axs_tables[1].set_title(team_b)



# Add match result and goal scorers to bottom of figure
summary_text = f"Result: {team_a} {goals_by_team.get(team_a, 0)} - {goals_by_team.get(team_b, 0)} {team_b}\n"

# Add goal scorers
summary_text += f"\nGoal Scorers {team_a}:\n"
scorers_a = goals[goals['team.name'] == team_a]['player.name'].value_counts()
if not scorers_a.empty:
    for player, count in scorers_a.items():
        summary_text += f"  - {player}: {count} Goal\n"
else:
    summary_text += "  No goals\n"


# Add footnote explanation
fig_tables.text(0.5, 0.01, summary_text, ha='center', fontsize=10, wrap=True)


plt.suptitle(f"xG Shot Map - {home_team} vs {away_team} ({match_date})", fontsize=14)
plt.tight_layout()
fig.text(0.5, 0.01, "🟢Green = Goal     🔴Red = Missed Shot", ha='center', fontsize=14, color='black')


# Save image
image_path = os.path.join(os.path.expanduser('~'), 'Desktop', f"{match_date}_{home_team}_vs_{away_team}_xG_Map.png")
# Check Existing Folder
image_folder = os.path.dirname(image_path)
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# save result
plt.savefig(image_path, dpi=300, bbox_inches='tight')

print(f" xG map image saved on Desktop: {image_path}")
plt.show()

