# Import the necessary PsychoPy libraries and other modules
from psychopy import visual, core, event, gui, parallel
import random
import csv
import configparser
import numpy as np
import os
import io 
from nogo_logic import select_nogo_trials_in_block

# --- Import helper functions from external files ---
from mind_wandering import show_mind_wandering_probe, load_mw_config
from quiz_logic import run_comprehension_quiz


# --- GUI for Participant Info ---
expInfo = {'participant': '1', 'session': '1', 'language': ['en', 'es']}
dlg = gui.DlgFromDict(dictionary=expInfo, title='Experiment Settings')
if not dlg.OK:
    core.quit()

# --- Load Experiment Settings from a separate file ---
config = configparser.ConfigParser()
try:
    config.read('experiment_settings.ini')
    TRIALS_PER_BLOCK = config.getint('Experiment', 'num_trials')
    NUM_BLOCKS = config.getint('Experiment', 'num_blocks')
    INTERFERENCE_EPOCH_ENABLED = config.getboolean('Experiment', 'interference_epoch_enabled')
    INTERFERENCE_EPOCH_NUM = config.getint('Experiment', 'interference_epoch_num')
    NO_GO_TRIALS_ENABLED = config.getboolean('Experiment', 'no_go_trials_enabled')
    NUM_NO_GO_TRIALS = config.getint('Experiment', 'num_no_go_trials')
    MW_TESTING_INVOLVED = config.getboolean('Experiment', 'mw_testing_involved')
    # Load the optional quiz setting
    RUN_COMPREHENSION_QUIZ = config.getboolean('Experiment', 'run_quiz_if_mw_enabled')
    PRACTICE_ENABLED = config.getboolean('Practice', 'practice_enabled')
    NUM_PRACTICE_BLOCKS = config.getint('Practice', 'num_practice_blocks')
    
except (configparser.Error, FileNotFoundError) as e:
    print(f"Error reading configuration file: {e}")
    core.quit()

# --- LOAD ALL EXPERIMENT TEXT ---
language_code = expInfo['language'] 
text_filename = f'experiment_text_{language_code}.ini' 

text_config = configparser.ConfigParser()

try:
    if not os.path.exists(text_filename):
        print(f"Error: Language file '{text_filename}' not found.")
        core.quit()

    # CRITICAL FIX: Use io.open with 'utf-8-sig' to handle BOM/accents robustly
    with io.open(text_filename, mode='r', encoding='utf-8-sig') as f:
        file_content = f.read()
    
    file_content = file_content.strip()
    text_config.read_string(file_content)
    
    if not text_config.sections():
        raise FileNotFoundError(f"Text configuration file '{text_filename}' is empty.")
except Exception as e:
    print(f"Error loading experiment text file: {e}")
    core.quit()

# Initialize helper module's config with the filename
load_mw_config(filename=text_filename) 

# --- HELPER FUNCTION DEFINED IN MAIN SCRIPT (for Instructions and Screens text) ---
def get_text_with_newlines(section, option, default=None):
    """Retrieves text and handles escape sequences for display in the main script."""
    global text_config 
    try:
        text_content = text_config.get(section, option, raw=True)
        return text_content.encode().decode('unicode_escape')
    except configparser.NoOptionError:
        if default is not None:
            return default
        else:
            raise

# --- Define a list of possible sequences ---
all_sequences = [
    [1, 2, 3, 4],
    [1, 2, 4, 3],
    [1, 3, 2, 4],
    [1, 3, 4, 2],
    [1, 4, 3, 2],
    [1, 4, 2, 3]
]

# Get the participant number and use it to select a sequence
participant_num = int(expInfo['participant'])
sequence_index = (participant_num - 1) % len(all_sequences)
pattern_sequence = all_sequences[sequence_index]

# Convert the selected pattern sequence to a string for easy saving
sequence_to_save = str(pattern_sequence).replace('[', '').replace(']', '').replace(' ', '')

# --- Setup the PsychoPy window and stimuli (CRITICAL FIXES HERE) ---
win = visual.Window(
    size=[1920, 1080],
    fullscr=True,
    monitor="testMonitor",
    units="pix",
    color='white',
    multiSample=True,
    numSamples=16,
    useFBO=True # CRITICAL FIX for accent rendering stability
)

# --- Define image paths ---
target_image_path = 'target_image.png' 
nogo_image_path = 'nogo_image.png'

# Define stimulus properties
circle_radius = 60
y_pos = 0.0
x_positions = [-240, -80, 80, 240]

# Create circle stimuli and their corresponding keys
stimuli = []
keys = ['s', 'f', 'j', 'l']
for x, key in zip(x_positions, keys):
    circle = visual.Circle(
        win=win,
        radius=circle_radius,
        fillColor='white',
        lineColor='black',
        lineWidth=3,
        pos=(x, y_pos)
    )
    stimuli.append({'stim': circle, 'key': key})

# State variables for the experiment
all_data = [] 
total_trial_count = 0
header_written = False
NA_MW_RATING = 'NA' 

# --- Initialize Parallel Port for Triggers ---
p_port = None
try:
    p_port = parallel.ParallelPort(address='0x0378') 
    p_port.setData(0)
    print(f"Parallel port initialized at address 0x0378.")
except Exception as e:
    print(f"Parallel port not found or could not be initialized. Error: {e}")
    print("Continuing without parallel port (triggers will be faked).")
    p_port = None

# --- Helper function for sending and resetting a trigger pulse ---
def send_trigger_pulse(trigger_value, pulse_duration=0.01):
    """Sends a trigger pulse (value, duration) and resets the port to 0."""
    if p_port:
        p_port.setData(trigger_value)
        core.wait(pulse_duration)
        p_port.setData(0)
    else:
        print(f"Faking parallel port trigger: {trigger_value}")

# Store positions of the last two trials for the 2-back check
pos_minus_1 = None
pos_minus_2 = None

# --- Helper function to save data and quit ---
def save_and_quit():
    data_folder = 'data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    
    filename = os.path.join(data_folder, f"participant_{expInfo['participant']}_session_{expInfo['session']}_data.csv")
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'probability_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'is_nogo', 'is_practice', 'epoch', 
                      'mind_wandering_rating_1', 'mind_wandering_rating_2', 'mind_wandering_rating_3', 'mind_wandering_rating_4'] 
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print("Experiment terminated early. Data saved successfully.")
    win.close()
    core.quit()

# --- Instruction Window ---
keys_list_str = ", ".join([f"'{k}'" for k in keys])
instruction_text = get_text_with_newlines('Instructions', 'welcome_screen').format(keys_list=keys_list_str)

instruction_message = visual.TextStim(
    win, text=instruction_text, color='black', height=30, wrapWidth=1000, alignHoriz='center', alignVert='center', font='Arial'
)

instruction_message.draw()
win.flip()

# Wait only for the spacebar press
key_pressed = event.waitKeys(keyList=['space', 'escape'])

if 'escape' in key_pressed:
    save_and_quit()
    
# --- Mind Wandering Probe Instructions (MADE OPTIONAL) ---

if MW_TESTING_INVOLVED:
    mw_instructions = [
        get_text_with_newlines('MW_Probes', 'mw_intro'),
        get_text_with_newlines('MW_Probes', 'mw_q1'),
        get_text_with_newlines('MW_Probes', 'mw_q2_off_task'),
        get_text_with_newlines('MW_Probes', 'mw_q3_spontaneous'),
        get_text_with_newlines('MW_Probes', 'mw_q4_affective'),
        get_text_with_newlines('MW_Probes', 'mw_on_task_follow_up'),
        get_text_with_newlines('MW_Probes', 'mw_final_note')
    ]

    for i, page_text in enumerate(mw_instructions):
        page_num = i + 1
        total_pages = len(mw_instructions)
        
        if page_num == total_pages:
            # Gating prompt text based on whether the quiz is enabled
            if not RUN_COMPREHENSION_QUIZ:
                 prompt_key = 'prompt_continue'
                 default_quiz_prompt = "(Press SPACE to continue to the main task.)"
            else:
                 prompt_key = 'prompt_quiz'
                 default_quiz_prompt = "(Press SPACE to continue to the quiz.)"
                 
            prompt_text = get_text_with_newlines('Screens', prompt_key, default=default_quiz_prompt)
        else:
            default_continue_prompt = "(Press SPACE to continue.)"
            prompt_text = get_text_with_newlines('Screens', 'prompt_continue', default=default_continue_prompt)

        combined_text = page_text + "\n\n" + prompt_text.strip()
        
        mw_message = visual.TextStim(
            win, text=combined_text, color='black', height=25, wrapWidth=1000, 
            alignHoriz='center', alignVert='center', font='Arial'
        )

        mw_message.draw()
        win.flip()

        key_pressed = event.waitKeys(keyList=['space', 'escape'])

        if 'escape' in key_pressed:
            save_and_quit()
            
    # --- Quiz Implementation (Gated by Setting) ---
    if RUN_COMPREHENSION_QUIZ:
        # Run the quiz only if MW is involved AND the quiz is explicitly enabled
        run_comprehension_quiz(win, save_and_quit, text_filename) 

# --- Initial 'Start Experiment' window ---
if PRACTICE_ENABLED:
    start_text = get_text_with_newlines('Screens', 'start_practice').format(NUM_PRACTICE_BLOCKS=NUM_PRACTICE_BLOCKS)
    start_trigger_value = 81
else:
    start_text = get_text_with_newlines('Screens', 'start_main')
    start_trigger_value = 11

start_message = visual.TextStim(win, text=start_text, color='black', height=40, wrapWidth=1000, font='Arial')
start_message.draw()
win.flip()

event.waitKeys()
if p_port:
    p_port.setData(start_trigger_value)
    core.wait(0.01)
    p_port.setData(0)
else:
    print(f"Faking parallel port trigger: {start_trigger_value}")

# --- Practice Loop ---
for practice_block_num in range(1, NUM_PRACTICE_BLOCKS + 1) if PRACTICE_ENABLED else []:
    block_data = []
    pos_minus_1 = None
    pos_minus_2 = None
    
    # ... (No-Go trial selection logic remains the same)
    nogo_trial_indices_in_block = set()
    if NO_GO_TRIALS_ENABLED:
        num_nogo_per_block = NUM_NO_GO_TRIALS
        num_nogo_p_per_block = 0
        num_nogo_r_per_block = num_nogo_per_block
        
        pre_block_trials = []
        for trial_in_block in range(TRIALS_PER_BLOCK):
            trial_in_block_num = trial_in_block + 1
            trial_type = 'R'
            pre_block_trials.append({'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type})
        block_indices = range(len(pre_block_trials))
        
        try:
            # CALL TO EXTERNAL FUNCTION
            nogo_indices_in_block_relative = select_nogo_trials_in_block(block_indices, pre_block_trials, num_nogo_p_per_block, num_nogo_r_per_block)
            nogo_trial_indices_in_block.update(nogo_indices_in_block_relative)
        except (ValueError, RuntimeError) as e:
            print(f"Error selecting no-go trials for Practice Block {practice_block_num}: {e}")
            core.quit()

    practice_positions_list = []
    positions_per_stim = TRIALS_PER_BLOCK // len(stimuli)
    for pos_num in range(1, len(stimuli) + 1):
        practice_positions_list.extend([pos_num] * positions_per_stim)
    random.shuffle(practice_positions_list)
    practice_list_index = 0
    
    # Define default NA ratings for the block
    na_ratings = [NA_MW_RATING] * 4

    for trial_in_block in range(TRIALS_PER_BLOCK):
        total_trial_count += 1
        trial_in_block_num = trial_in_block + 1
        is_nogo = (trial_in_block in nogo_trial_indices_in_block)

        if 'escape' in event.getKeys():
            save_and_quit()

        for stim_dict in stimuli:
            stim_dict['stim'].fillColor = 'white'
        for stim_dict in stimuli:
            stim_dict['stim'].draw()
        win.flip()
        core.wait(0.120)

        target_stim_pos = practice_positions_list[practice_list_index]
        practice_list_index += 1
        trial_type = 'R'
        probability_type = 'X'

        pos_minus_2 = pos_minus_1
        pos_minus_1 = target_stim_pos
        
        target_stim_index = target_stim_pos - 1
        if is_nogo:
            image_path_to_use = nogo_image_path
        else:
            image_path_to_use = target_image_path
            
        stimuli[target_stim_index]['stim'].fillColor = 'blue'
        border_circle = visual.Circle(
            win=win,
            radius=circle_radius,
            fillColor='black',
            pos=stimuli[target_stim_index]['stim'].pos
        )
        image_size = circle_radius * 2 - 3
        target_image = visual.ImageStim(
            win=win,
            image=image_path_to_use,
            size=image_size,
            pos=stimuli[target_stim_index]['stim'].pos
        )
        
        if is_nogo:
            trial_trigger = 251 + target_stim_pos
        else:
            trial_trigger = 151 + target_stim_pos

        if p_port:
            p_port.setData(trial_trigger)
            core.wait(0.01)
            p_port.setData(0)
        else:
            print(f"Faking parallel port trigger: {trial_trigger}")
        print(f"Trial {total_trial_count} onset trigger: {trial_trigger} (Type: {trial_type}, Pos: {target_stim_pos}, Prob: {probability_type})")

        cumulative_timer = core.Clock()
        
        if is_nogo:
            response_logged = False
            
            while cumulative_timer.getTime() < 1.0:
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
            
                responses = event.getKeys(keyList=keys + ['escape'], timeStamped=cumulative_timer)
                if responses and not response_logged:
                    pressed_key, rt = responses[0]
                    
                    if pressed_key == 'escape':
                        save_and_quit()

                    was_correct = False
                    rt_cumulative = rt
                    rt_non_cumulative = rt
                    pressed_key_pos = keys.index(pressed_key) + 1
                    response_trigger = 341 + pressed_key_pos
                    
                    if p_port:
                        p_port.setData(response_trigger)
                        core.wait(0.01)
                        p_port.setData(0)
                    else:
                        print(f"Faking parallel port trigger: {response_trigger}")
                    print(f"Response trigger: {response_trigger} (No-Go Error)")
                    
                    block_data.append({
                        'participant': expInfo['participant'],
                        'session': expInfo['session'],
                        'block_number': practice_block_num,
                        'trial_number': total_trial_count,
                        'trial_in_block_num': trial_in_block_num,
                        'trial_type': trial_type,
                        'probability_type': probability_type,
                        'sequence_used': sequence_to_save,
                        'stimulus_position_num': target_stim_pos,
                        'rt_non_cumulative_s': rt_non_cumulative,
                        'rt_cumulative_s': rt_cumulative,
                        'correct_key_pressed': 'NoGo',
                        'response_key_pressed': pressed_key,
                        'correct_response': was_correct,
                        'is_nogo': True,
                        'is_practice': True,
                        'epoch': 0,
                        'mind_wandering_rating_1': na_ratings[0], 
                        'mind_wandering_rating_2': na_ratings[1],
                        'mind_wandering_rating_3': na_ratings[2],
                        'mind_wandering_rating_4': na_ratings[3]
                    })
                    response_logged = True
            
            if not response_logged:
                    block_data.append({
                        'participant': expInfo['participant'],
                        'session': expInfo['session'],
                        'block_number': practice_block_num,
                        'trial_number': total_trial_count,
                        'trial_in_block_num': trial_in_block_num,
                        'trial_type': trial_type,
                        'probability_type': probability_type,
                        'sequence_used': sequence_to_save,
                        'stimulus_position_num': target_stim_pos,
                        'rt_non_cumulative_s': None,
                        'rt_cumulative_s': None,
                        'correct_key_pressed': 'NoGo',
                        'response_key_pressed': 'None',
                        'correct_response': True,
                        'is_nogo': True,
                        'is_practice': True,
                        'epoch': 0,
                        'mind_wandering_rating_1': na_ratings[0], 
                        'mind_wandering_rating_2': na_ratings[1],
                        'mind_wandering_rating_3': na_ratings[2],
                        'mind_wandering_rating_4': na_ratings[3]
                    })
        
        else: # This is a regular go trial
            response_timer = core.Clock()
            correct_response_given = False
            while not correct_response_given:
                if 'escape' in event.getKeys():
                    save_and_quit()
            
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
            
                response_keys = event.getKeys(keyList=keys + ['escape'])
            
                if response_keys:
                    pressed_key = response_keys[0]
                
                    if pressed_key == 'escape':
                        save_and_quit()
                    rt_non_cumulative = response_timer.getTime()
                    rt_cumulative = cumulative_timer.getTime()
                
                    was_correct = (pressed_key == stimuli[target_stim_index]['key'])
                    pressed_key_pos = keys.index(pressed_key) + 1
                    
                    if was_correct:
                        response_type_base = 321
                        response_trigger = response_type_base + pressed_key_pos
                    else:
                        incorrect_response_base = 331
                        response_trigger = incorrect_response_base + pressed_key_pos
                    
                    if p_port:
                        p_port.setData(response_trigger)
                        core.wait(0.01)
                        p_port.setData(0)
                    else:
                        print(f"Faking parallel port trigger: {response_trigger}")
                    print(f"Response trigger: {response_trigger} (Type: {trial_type}, Correct: {was_correct}, Key Pos: {pressed_key_pos})")

                    block_data.append({
                        'participant': expInfo['participant'],
                        'session': expInfo['session'],
                        'block_number': practice_block_num,
                        'trial_number': total_trial_count,
                        'trial_in_block_num': trial_in_block_num,
                        'trial_type': trial_type,
                        'probability_type': probability_type,
                        'sequence_used': sequence_to_save,
                        'stimulus_position_num': target_stim_pos,
                        'rt_non_cumulative_s': rt_non_cumulative,
                        'rt_cumulative_s': rt_cumulative,
                        'correct_key_pressed': stimuli[target_stim_index]['key'],
                        'response_key_pressed': pressed_key,
                        'correct_response': was_correct,
                        'is_nogo': False,
                        'is_practice': True,
                        'epoch': 0,
                        'mind_wandering_rating_1': na_ratings[0], 
                        'mind_wandering_rating_2': na_ratings[1],
                        'mind_wandering_rating_3': na_ratings[2],
                        'mind_wandering_rating_4': na_ratings[3]
                    })
                
                    response_timer.reset()

                    if was_correct:
                        correct_response_given = True
        
        if 'escape' in event.getKeys():
            save_and_quit()

    # --- Mind Wandering Probe for Practice Block ---
    mw_ratings = show_mind_wandering_probe(win, MW_TESTING_INVOLVED, NA_MW_RATING, save_and_quit)
    
    for d in block_data:
        d['mind_wandering_rating_1'] = mw_ratings[0]
        d['mind_wandering_rating_2'] = mw_ratings[1]
        d['mind_wandering_rating_3'] = mw_ratings[2]
        d['mind_wandering_rating_4'] = mw_ratings[3]

    all_data.extend(block_data)
    
    # --- Save data after each block ---
    data_folder = 'data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    
    filename = os.path.join(data_folder, f"participant_{expInfo['participant']}_session_{expInfo['session']}_data.csv")
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'probability_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'is_nogo', 'is_practice', 'epoch', 
                      'mind_wandering_rating_1', 'mind_wandering_rating_2', 'mind_wandering_rating_3', 'mind_wandering_rating_4']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Data for Practice Block {practice_block_num} saved successfully.")

    # --- Display feedback for 3 seconds ---
    correct_rts = [d['rt_cumulative_s'] for d in block_data if d['correct_response'] and not d['is_nogo']]
    total_correct_responses = sum(1 for d in block_data if d['correct_response'] and not d['is_nogo'])
    total_responses = len([d for d in block_data if not d['is_nogo']])

    mean_rt = np.mean(correct_rts) if correct_rts else 0
    accuracy = (total_correct_responses / total_responses) * 100 if total_responses > 0 else 0
    
    if accuracy < 90:
        performance_message = get_text_with_newlines('Screens', 'feedback_accurate')
        performance_color = 'red'
    elif mean_rt > 0.350:
        performance_message = get_text_with_newlines('Screens', 'feedback_faster')
        performance_color = 'red'
    else:
        performance_message = get_text_with_newlines('Screens', 'feedback_good_job')
        performance_color = 'green'

    feedback_header_text = get_text_with_newlines('Screens', 'feedback_header').format(block_num=practice_block_num)
    feedback_stats_text = f"Mean RT: {mean_rt:.2f} s\nAccuracy: {accuracy:.2f} %"
    
    feedback_header = visual.TextStim(win, text=feedback_header_text, color='black', height=40, pos=(0, 100), wrapWidth=1000, font='Arial')
    feedback_stats = visual.TextStim(win, text=feedback_stats_text, color='black', height=30, pos=(0, 0), wrapWidth=1000, font='Arial')
    feedback_performance = visual.TextStim(win, text=performance_message, color=performance_color, height=40, pos=(0, -100), wrapWidth=1000, font='Arial')
    
    win.flip()
    feedback_header.draw()
    feedback_stats.draw()
    feedback_performance.draw()

    trigger_base = 40
    if p_port:
        p_port.setData(trigger_base + practice_block_num)
        core.wait(0.01)
        p_port.setData(0)
    else:
        print(f"Faking parallel port trigger: {trigger_base + practice_block_num}")
    win.flip()
    core.wait(3)

    if practice_block_num < NUM_PRACTICE_BLOCKS:
        continuation_text = get_text_with_newlines('Screens', 'next_practice')
        continuation_message = visual.TextStim(win, text=continuation_text, color='black', height=40, wrapWidth=1000, font='Arial')
        win.flip()
        continuation_message.draw()
        win.flip()
        event.waitKeys()
        if 'escape' in event.getKeys():
            save_and_quit()

        trigger_base = 80
        if p_port:
            p_port.setData(trigger_base + (practice_block_num + 1))
            core.wait(0.01)
            p_port.setData(0)
        else:
            print(f"Faking parallel port trigger: {trigger_base + (practice_block_num + 1)}")
    
if PRACTICE_ENABLED:
    end_practice_text = get_text_with_newlines('Screens', 'end_practice')
    end_practice_message = visual.TextStim(win, text=end_practice_text, color='black', height=40, wrapWidth=1000, font='Arial')
    
    win.flip()
    end_practice_message.draw()
    win.flip()
    event.waitKeys()
    if 'escape' in event.getKeys():
        save_and_quit()
    if p_port:
        p_port.setData(99)
        core.wait(0.01)
        p_port.setData(0)
    else:
        print(f"Faking parallel port trigger: 99")

# --- Main Experiment Loop ---
for block_num in range(1, NUM_BLOCKS + 1):
    block_data = []
    pattern_index = 0
    pos_minus_1 = None
    pos_minus_2 = None
    current_pattern_sequence = list(pattern_sequence)
    random_list_index = 0
    
    epoch = ((block_num - 1) // 5) + 1
    if INTERFERENCE_EPOCH_ENABLED and epoch == INTERFERENCE_EPOCH_NUM:
        if current_pattern_sequence == list(pattern_sequence):
            current_pattern_sequence.reverse()
    elif current_pattern_sequence != list(pattern_sequence) and epoch != INTERFERENCE_EPOCH_NUM:
        current_pattern_sequence = list(pattern_sequence)
    
    # --- FIX: Generate and shuffle the random trial positions once per block ---
    
    num_random_trials = TRIALS_PER_BLOCK - (TRIALS_PER_BLOCK // 2)

    random_positions_list = []
    positions_per_stim = num_random_trials // len(stimuli)
    
    if num_random_trials % len(stimuli) != 0:
        print("Warning: Number of random trials is not evenly divisible by number of stimuli. Random positions won't be perfectly counterbalanced.")

    for pos_num in range(1, len(stimuli) + 1):
        random_positions_list.extend([pos_num] * positions_per_stim)
        
    random.shuffle(random_positions_list)
    
    # --- END FIX ---

    nogo_trial_indices_in_block = set()
    if NO_GO_TRIALS_ENABLED:
        num_nogo_per_block = NUM_NO_GO_TRIALS
        num_nogo_p_per_block = num_nogo_per_block // 2
        num_nogo_r_per_block = num_nogo_per_block - num_nogo_p_per_block

        pre_block_trials = []
        for trial_in_block in range(TRIALS_PER_BLOCK):
            trial_in_block_num = trial_in_block + 1
            if trial_in_block_num % 2 == 0:
                trial_type = 'P'
            else:
                trial_type = 'R'
            pre_block_trials.append({'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type})
        block_indices = range(len(pre_block_trials))
        
        try:
            nogo_indices_in_block = select_nogo_trials_in_block(block_indices, pre_block_trials, num_nogo_p_per_block, num_nogo_r_per_block)
            nogo_trial_indices_in_block.update(nogo_indices_in_block)
        except (ValueError, RuntimeError) as e:
            print(f"Error selecting no-go trials for Main Block {block_num}: {e}")
            core.quit()

    # Define default NA ratings for the block
    na_ratings = [NA_MW_RATING] * 4

    for trial_in_block in range(TRIALS_PER_BLOCK):
        total_trial_count += 1
        trial_in_block_num = trial_in_block + 1
        is_nogo = (trial_in_block in nogo_trial_indices_in_block)

        if 'escape' in event.getKeys():
            save_and_quit()

        for stim_dict in stimuli:
            stim_dict['stim'].fillColor = 'white'
        
        for stim_dict in stimuli:
            stim_dict['stim'].draw()
        win.flip()
        core.wait(0.120)

        if trial_in_block_num % 2 == 0:
            # Pattern trial (Even trial number)
            target_stim_pos = current_pattern_sequence[pattern_index]
            pattern_index = (pattern_index + 1) % len(current_pattern_sequence)
            trial_type = 'P'
        else:
            # Random trial (Odd trial number)
            target_stim_pos = random_positions_list[random_list_index]
            random_list_index += 1
            trial_type = 'R'

        probability_type = 'L'
        if trial_type == 'P':
            probability_type = 'H'
        else:
            if pos_minus_2 is not None:
                try:
                    two_back_pos_idx = current_pattern_sequence.index(pos_minus_2)
                    current_pos_idx = current_pattern_sequence.index(target_stim_pos)
                    expected_two_back_pos = current_pattern_sequence[(current_pos_idx - 1) % len(current_pattern_sequence)]
                
                    if pos_minus_2 == expected_two_back_pos:
                        probability_type = 'H'
                    elif pos_minus_2 == target_stim_pos:
                        probability_type = 'T'
                        if pos_minus_1 is not None and pos_minus_1 == target_stim_pos:
                            probability_type = 'R'
                except ValueError:
                    probability_type = 'L'

        if trial_in_block_num <= 2:
            probability_type = 'X'
        
        if is_nogo:
            if trial_type == 'P' and probability_type == 'H':
                trial_trigger = 201 + target_stim_pos
            elif trial_type == 'R' and probability_type == 'H':
                trial_trigger = 211 + target_stim_pos
            elif probability_type == 'L':
                trial_trigger = 221 + target_stim_pos
            elif probability_type == 'T':
                trial_trigger = 231 + target_stim_pos
            elif probability_type == 'R':
                trial_trigger = 241 + target_stim_pos
            elif probability_type == 'X':
                trial_trigger = 251 + target_stim_pos
        else:
            if trial_type == 'P':
                trial_trigger = 101 + target_stim_pos
            else:
                if probability_type == 'H':
                    trial_trigger = 111 + target_stim_pos
                elif probability_type == 'L':
                    trial_trigger = 121 + target_stim_pos
                elif probability_type == 'T':
                    trial_trigger = 131 + target_stim_pos
                elif probability_type == 'R':
                    trial_trigger = 141 + target_stim_pos
                elif probability_type == 'X':
                    trial_trigger = 151 + target_stim_pos

        pos_minus_2 = pos_minus_1
        pos_minus_1 = target_stim_pos
            
        target_stim_index = target_stim_pos - 1
        if is_nogo:
            image_path_to_use = nogo_image_path
        else:
            image_path_to_use = target_image_path
            
        stimuli[target_stim_index]['stim'].fillColor = 'blue'
        border_circle = visual.Circle(
            win=win,
            radius=circle_radius,
            fillColor='black',
            pos=stimuli[target_stim_index]['stim'].pos
        )
        image_size = circle_radius * 2 - 3
        target_image = visual.ImageStim(
            win=win,
            image=image_path_to_use,
            size=image_size,
            pos=stimuli[target_stim_index]['stim'].pos
        )
        
        if p_port:
            p_port.setData(trial_trigger)
            core.wait(0.01)
            p_port.setData(0)
        else:
            print(f"Faking parallel port trigger: {trial_trigger}")
        print(f"Trial {total_trial_count} onset trigger: {trial_trigger} (Type: {trial_type}, Pos: {target_stim_pos}, Prob: {probability_type})")

        cumulative_timer = core.Clock()
        
        if is_nogo:
            response_logged = False
            
            while cumulative_timer.getTime() < 1.0:
                if 'escape' in event.getKeys():
                    save_and_quit()
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
            
                responses = event.getKeys(keyList=keys + ['escape'], timeStamped=cumulative_timer)
                if responses and not response_logged:
                    pressed_key, rt = responses[0]
                    
                    if pressed_key == 'escape':
                        save_and_quit()

                    was_correct = False
                    rt_cumulative = rt
                    rt_non_cumulative = rt
                    pressed_key_pos = keys.index(pressed_key) + 1
                    response_trigger = 341 + pressed_key_pos
                    
                    if p_port:
                        p_port.setData(response_trigger)
                        core.wait(0.01)
                        p_port.setData(0)
                    else:
                        print(f"Faking parallel port trigger: {response_trigger}")
                    print(f"Response trigger: {response_trigger} (No-Go Error)")
                    
                    block_data.append({
                        'participant': expInfo['participant'],
                        'session': expInfo['session'],
                        'block_number': block_num,
                        'trial_number': total_trial_count,
                        'trial_in_block_num': trial_in_block_num,
                        'trial_type': trial_type,
                        'probability_type': probability_type,
                        'sequence_used': sequence_to_save,
                        'stimulus_position_num': target_stim_pos,
                        'rt_non_cumulative_s': rt_non_cumulative,
                        'rt_cumulative_s': rt_cumulative,
                        'correct_key_pressed': 'NoGo',
                        'response_key_pressed': pressed_key,
                        'correct_response': was_correct,
                        'is_nogo': True,
                        'is_practice': False,
                        'epoch': epoch,
                        'mind_wandering_rating_1': na_ratings[0], 
                        'mind_wandering_rating_2': na_ratings[1],
                        'mind_wandering_rating_3': na_ratings[2],
                        'mind_wandering_rating_4': na_ratings[3]
                    })
                    response_logged = True
            
            if not response_logged:
                    block_data.append({
                        'participant': expInfo['participant'],
                        'session': expInfo['session'],
                        'block_number': block_num,
                        'trial_number': total_trial_count,
                        'trial_in_block_num': trial_in_block_num,
                        'trial_type': trial_type,
                        'probability_type': probability_type,
                        'sequence_used': sequence_to_save,
                        'stimulus_position_num': target_stim_pos,
                        'rt_non_cumulative_s': None,
                        'rt_cumulative_s': None,
                        'correct_key_pressed': 'NoGo',
                        'response_key_pressed': 'None',
                        'correct_response': True,
                        'is_nogo': True,
                        'is_practice': False,
                        'epoch': epoch,
                        'mind_wandering_rating_1': na_ratings[0], 
                        'mind_wandering_rating_2': na_ratings[1],
                        'mind_wandering_rating_3': na_ratings[2],
                        'mind_wandering_rating_4': na_ratings[3]
                    })
        
        else: # This is a regular go trial
            response_timer = core.Clock()
            correct_response_given = False
            while not correct_response_given:
                if 'escape' in event.getKeys():
                    save_and_quit()
            
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
            
                response_keys = event.getKeys(keyList=keys + ['escape'])
            
                if response_keys:
                    pressed_key = response_keys[0]
                
                    if pressed_key == 'escape':
                        save_and_quit()
                    rt_non_cumulative = response_timer.getTime()
                    rt_cumulative = cumulative_timer.getTime()
                
                    was_correct = (pressed_key == stimuli[target_stim_index]['key'])
                    pressed_key_pos = keys.index(pressed_key) + 1
                    
                    if was_correct:
                        response_type_base = 301 if trial_type == 'P' else 321
                        response_trigger = response_type_base + pressed_key_pos
                    else:
                        incorrect_response_base = 311 if trial_type == 'P' else 331
                        response_trigger = incorrect_response_base + pressed_key_pos
                    
                    if p_port:
                        p_port.setData(response_trigger)
                        core.wait(0.01)
                        p_port.setData(0)
                    else:
                        print(f"Faking parallel port trigger: {response_trigger}")
                    print(f"Response trigger: {response_trigger} (Type: {trial_type}, Correct: {was_correct}, Key Pos: {pressed_key_pos})")

                    block_data.append({
                        'participant': expInfo['participant'],
                        'session': expInfo['session'],
                        'block_number': block_num,
                        'trial_number': total_trial_count,
                        'trial_in_block_num': trial_in_block_num,
                        'trial_type': trial_type,
                        'probability_type': probability_type,
                        'sequence_used': sequence_to_save,
                        'stimulus_position_num': target_stim_pos,
                        'rt_non_cumulative_s': rt_non_cumulative,
                        'rt_cumulative_s': rt_cumulative,
                        'correct_key_pressed': stimuli[target_stim_index]['key'],
                        'response_key_pressed': pressed_key,
                        'correct_response': was_correct,
                        'is_nogo': False,
                        'is_practice': False,
                        'epoch': epoch,
                        'mind_wandering_rating_1': na_ratings[0], 
                        'mind_wandering_rating_2': na_ratings[1],
                        'mind_wandering_rating_3': na_ratings[2],
                        'mind_wandering_rating_4': na_ratings[3]
                    })
                
                    response_timer.reset()

                    if was_correct:
                        correct_response_given = True
        
        if 'escape' in event.getKeys():
            save_and_quit()
    
    # --- Mind Wandering Probe for Main Block ---
    mw_ratings = show_mind_wandering_probe(win, MW_TESTING_INVOLVED, NA_MW_RATING, save_and_quit)
    
    for d in block_data:
        d['mind_wandering_rating_1'] = mw_ratings[0]
        d['mind_wandering_rating_2'] = mw_ratings[1]
        d['mind_wandering_rating_3'] = mw_ratings[2]
        d['mind_wandering_rating_4'] = mw_ratings[3]

    all_data.extend(block_data)
    
    # --- Save data after each block ---
    data_folder = 'data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    filename = os.path.join(data_folder, f"participant_{expInfo['participant']}_session_{expInfo['session']}_data.csv")
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'probability_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'is_nogo', 'is_practice', 'epoch', 
                      'mind_wandering_rating_1', 'mind_wandering_rating_2', 'mind_wandering_rating_3', 'mind_wandering_rating_4']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Data for Main Block {block_num} saved successfully.")

    # --- Display feedback for 3 seconds ---
    correct_rts = [d['rt_cumulative_s'] for d in block_data if d['correct_response'] and not d['is_nogo']]
    total_correct_responses = sum(1 for d in block_data if d['correct_response'] and not d['is_nogo'])
    total_responses = len([d for d in block_data if not d['is_nogo']])

    mean_rt = np.mean(correct_rts) if correct_rts else 0
    accuracy = (total_correct_responses / total_responses) * 100 if total_responses > 0 else 0
    
    if accuracy < 90:
        performance_message = get_text_with_newlines('Screens', 'feedback_accurate')
        performance_color = 'red'
    elif mean_rt > 0.350:
        performance_message = get_text_with_newlines('Screens', 'feedback_faster')
        performance_color = 'red'
    else:
        performance_message = get_text_with_newlines('Screens', 'feedback_good_job')
        performance_color = 'green'

    feedback_header_text = get_text_with_newlines('Screens', 'feedback_header').format(block_num=block_num)
    feedback_stats_text = f"Mean RT: {mean_rt:.2f} s\nAccuracy: {accuracy:.2f} %"
    
    feedback_header = visual.TextStim(win, text=feedback_header_text, color='black', height=40, pos=(0, 100), wrapWidth=1000, font='Arial')
    feedback_stats = visual.TextStim(win, text=feedback_stats_text, color='black', height=30, pos=(0, 0), wrapWidth=1000, font='Arial')
    feedback_performance = visual.TextStim(win, text=performance_message, color=performance_color, height=40, pos=(0, -100), wrapWidth=1000, font='Arial')
    
    win.flip()
    feedback_header.draw()
    feedback_stats.draw()
    feedback_performance.draw()

    trigger_base = 20
    if p_port:
        p_port.setData(trigger_base + block_num)
        core.wait(0.01)
        p_port.setData(0)
    else:
        print(f"Faking parallel port trigger: {trigger_base + block_num}")
    win.flip()
    core.wait(3)

    if block_num < NUM_BLOCKS:
        continuation_text = get_text_with_newlines('Screens', 'next_main')
        continuation_message = visual.TextStim(win, text=continuation_text, color='black', height=40, wrapWidth=1000, font='Arial')
        win.flip()
        continuation_message.draw()
        win.flip()
        event.waitKeys()
        if 'escape' in event.getKeys():
            save_and_quit()

        trigger_base = 10
        if p_port:
            p_port.setData(trigger_base + (block_num + 1))
            core.wait(0.01)
            p_port.setData(0)
        else:
            print(f"Faking parallel port trigger: {trigger_base + (block_num + 1)}")

# --- End of Experiment message ---
print("Data saved successfully.")
end_text = get_text_with_newlines('Screens', 'end_experiment')
end_message = visual.TextStim(win, text=end_text, color='black', height=40, wrapWidth=1000, font='Arial')
end_message.draw()
win.flip()
event.waitKeys()
if 'escape' in event.getKeys():
    save_and_quit()
win.close()
core.quit()