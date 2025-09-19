# Import the necessary PsychoPy libraries and other modules
from psychopy import visual, core, event, gui, parallel
import random
import csv
import configparser
import numpy as np
import os

# --- GUI for Participant Info ---
expInfo = {'participant': '1', 'session': '1'}
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
    PRACTICE_ENABLED = config.getboolean('Practice', 'practice_enabled')
    NUM_PRACTICE_BLOCKS = config.getint('Practice', 'num_practice_blocks')
except (configparser.Error, FileNotFoundError) as e:
    print(f"Error reading configuration file: {e}")
    core.quit()

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

# --- Setup the PsychoPy window and stimuli ---
win = visual.Window(
    size=[1024, 768],
    fullscr=True,
    monitor="testMonitor",
    units="pix",
    color='white',
    multiSample=True,
    numSamples=16
)

# --- Define image path ---
target_image_path = 'target_image.png'

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
all_data = [] # To save all trial data cumulatively
total_trial_count = 0
header_written = False

# --- Initialize Parallel Port for Triggers ---
try:
    p_port = parallel.ParallelPort(address='0x0378')
    p_port.setData(0)
    print("Parallel port initialized.")
except Exception as e:
    print(f"Parallel port not found or could not be initialized: {e}")
    p_port = None
    
# Store positions of the last two trials for the 2-back check
pos_minus_1 = None
pos_minus_2 = None

# --- Initial 'Start Experiment' window ---
if PRACTICE_ENABLED:
    start_text = f"Practice blocks are enabled. Press any key to start the {NUM_PRACTICE_BLOCKS} practice blocks."
    start_trigger_value = 80 + 1  # Block 1 of practice
else:
    start_text = "Press any key to start the experiment."
    start_trigger_value = 10 + 1  # Block 1 of main experiment

start_message = visual.TextStim(win, text=start_text, color='black', height=40, wrapWidth=1000)
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
if PRACTICE_ENABLED:
    for practice_block_num in range(1, NUM_PRACTICE_BLOCKS + 1):
        block_data = []
        
        # Create a balanced list of random trial positions for this practice block
        practice_positions_list = []
        num_practice_trials = TRIALS_PER_BLOCK
        positions_per_stim = num_practice_trials // len(stimuli)
        for pos_num in range(1, len(stimuli) + 1):
            practice_positions_list.extend([pos_num] * positions_per_stim)
        random.shuffle(practice_positions_list)
        practice_list_index = 0
        
        for trial_in_block in range(TRIALS_PER_BLOCK):
            total_trial_count += 1
            trial_in_block_num = trial_in_block + 1
            if 'escape' in event.getKeys():
                break

            for stim_dict in stimuli:
                stim_dict['stim'].fillColor = 'white'
        
            for stim_dict in stimuli:
                stim_dict['stim'].draw()
            win.flip()
            core.wait(0.120)

            # Practice trials are always random
            target_stim_pos = practice_positions_list[practice_list_index]
            practice_list_index += 1
            trial_type = 'R'
            probability_type = 'X'
            trial_trigger = 65  # Special trigger for 'X' probability

            # Update the positions of the last two trials
            pos_minus_2 = pos_minus_1
            pos_minus_1 = target_stim_pos

            target_stim_index = target_stim_pos - 1
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
                image=target_image_path,
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
            response_timer = core.Clock()
        
            correct_response_given = False
            while not correct_response_given:
                if 'escape' in event.getKeys():
                    break
            
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
            
                response_keys = event.getKeys(keyList=keys + ['escape'])
            
                if response_keys:
                    pressed_key = response_keys[0]
                
                    if pressed_key == 'escape':
                        break
                
                    rt_non_cumulative = response_timer.getTime()
                    rt_cumulative = cumulative_timer.getTime()
                
                    was_correct = (pressed_key == stimuli[target_stim_index]['key'])
                    pressed_key_pos = keys.index(pressed_key) + 1
                
                    if was_correct:
                        response_trigger = 130 + pressed_key_pos
                    else:
                        response_trigger = 140 + pressed_key_pos
                    
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
                        'trial_in_block_num': trial_in_block + 1,
                        'trial_type': trial_type,
                        'probability_type': probability_type,
                        'sequence_used': sequence_to_save,
                        'stimulus_position_num': target_stim_pos,
                        'rt_non_cumulative_s': rt_non_cumulative,
                        'rt_cumulative_s': rt_cumulative,
                        'correct_key_pressed': stimuli[target_stim_index]['key'],
                        'response_key_pressed': pressed_key,
                        'correct_response': was_correct,
                        'epoch': 0
                    })
                
                    response_timer.reset()
    
                    if was_correct:
                        correct_response_given = True
            
            if 'escape' in event.getKeys():
                break

        all_data.extend(block_data)
        
        # --- Display feedback for 3 seconds ---
        correct_rts = [d['rt_cumulative_s'] for d in block_data if d['correct_response']]
        total_correct_responses = sum(1 for d in block_data if d['correct_response'])
        total_responses = len(block_data)

        mean_rt = np.mean(correct_rts) if correct_rts else 0
        accuracy = (total_correct_responses / total_responses) * 100 if total_responses > 0 else 0
        
        # New conditional feedback logic for practice blocks
        if accuracy < 90:
            performance_message = "Please try to be more accurate."
            performance_color = 'red'
        elif mean_rt > 0.350:
            performance_message = "Please try to be faster."
            performance_color = 'red'
        else:
            performance_message = "Good job."
            performance_color = 'green'

        feedback_header_text = f"End of Practice Block {practice_block_num} feedback:"
        feedback_stats_text = f"Mean RT: {mean_rt:.2f} s\nAccuracy: {accuracy:.2f} %"

        feedback_header = visual.TextStim(win, text=feedback_header_text, color='black', height=40, pos=(0, 100))
        feedback_stats = visual.TextStim(win, text=feedback_stats_text, color='black', height=30, pos=(0, 0))
        feedback_performance = visual.TextStim(win, text=performance_message, color=performance_color, height=40, pos=(0, -100))
        
        win.flip()
        feedback_header.draw()
        feedback_stats.draw()
        feedback_performance.draw()

        if p_port:
            p_port.setData(40 + practice_block_num)
            core.wait(0.01)
            p_port.setData(0)
        else:
            print(f"Faking parallel port trigger: {40 + practice_block_num}")

        win.flip()
        core.wait(3) # Wait for 3 seconds

        # --- Display continuation message on a separate screen ---
        if practice_block_num < NUM_PRACTICE_BLOCKS:
            continuation_text = "Press any key to start the next practice block."
            continuation_message = visual.TextStim(win, text=continuation_text, color='black', height=40, wrapWidth=1000)
            
            win.flip()
            continuation_message.draw()
            win.flip()

            event.waitKeys()
            if p_port:
                p_port.setData(80 + (practice_block_num + 1))
                core.wait(0.01)
                p_port.setData(0)
            else:
                print(f"Faking parallel port trigger: {80 + (practice_block_num + 1)}")
    
    # --- Transition to Main Experiment ---
    end_practice_text = "Practice is complete. Press any key to start the main experiment."
    end_practice_message = visual.TextStim(win, text=end_practice_text, color='black', height=40, wrapWidth=1000)
    
    win.flip()
    end_practice_message.draw()
    win.flip()
    event.waitKeys()
    if p_port:
        p_port.setData(99) # Main experiment starts
        core.wait(0.01)
        p_port.setData(0)
    else:
        print(f"Faking parallel port trigger: 99")

# --- Main Experiment Loop ---
for block_num in range(1, NUM_BLOCKS + 1):
    block_data = []
    pattern_index = 0
    
    # Calculate the current epoch number
    epoch = (block_num - 1) // 5 + 1
    
    # Check if this is the interference epoch and reverse the sequence if needed
    current_pattern_sequence = list(pattern_sequence)
    if INTERFERENCE_EPOCH_ENABLED and epoch == INTERFERENCE_EPOCH_NUM:
        current_pattern_sequence.reverse()
        print(f"--- Entering Interference Epoch {epoch} - Sequence is reversed ---")
        sequence_to_save_current = str(current_pattern_sequence).replace('[', '').replace(']', '').replace(' ', '')
    else:
        sequence_to_save_current = sequence_to_save
    
    # New: Create a balanced list of random trial positions for this block
    random_positions_list = []
    num_random_trials = TRIALS_PER_BLOCK // 2
    positions_per_stim = num_random_trials // len(stimuli)
    for pos_num in range(1, len(stimuli) + 1):
        random_positions_list.extend([pos_num] * positions_per_stim)
    random.shuffle(random_positions_list)
    random_list_index = 0 # To track position in the list

    for trial_in_block in range(TRIALS_PER_BLOCK):
        total_trial_count += 1
        trial_in_block_num = trial_in_block + 1
        if 'escape' in event.getKeys():
            break

        for stim_dict in stimuli:
            stim_dict['stim'].fillColor = 'white'
    
        for stim_dict in stimuli:
            stim_dict['stim'].draw()
        win.flip()
        core.wait(0.120)

        # Determine the trial type and the target circle position (1-4)
        if trial_in_block_num % 2 == 0:
            target_stim_pos = current_pattern_sequence[pattern_index]
            pattern_index = (pattern_index + 1) % len(current_pattern_sequence)
            trial_type = 'P'
            response_type_base = 110
            incorrect_response_base = 120
        else:
            # Get the next position from the pre-shuffled list
            target_stim_pos = random_positions_list[random_list_index]
            random_list_index += 1
            trial_type = 'R'
            response_type_base = 130
            incorrect_response_base = 140
    
        # --- Calculate Probability based on the n-2 and n-1 position rule ---
        probability_type = 'L'  # Default to Low
        if trial_type == 'P':
            probability_type = 'H'
        else:
            if pos_minus_2 is not None:
                try:
                    two_back_pos_idx = current_pattern_sequence.index(pos_minus_2)
                    current_pos_idx = current_pattern_sequence.index(target_stim_pos)
                    expected_two_back_pos = current_pattern_sequence[(current_pos_idx - 1) % len(current_pattern_sequence)]
                
                    # Case 1: n-2 position follows the n position
                    if pos_minus_2 == expected_two_back_pos:
                        probability_type = 'H'
                    # Case 2: n-2 position is the same as the n position
                    elif pos_minus_2 == target_stim_pos:
                        probability_type = 'T'
                        # Case 3: n-1 is also the same as n
                        if pos_minus_1 is not None and pos_minus_1 == target_stim_pos:
                            probability_type = 'R'
                except ValueError:
                    # If pos_minus_2 or target_stim_pos is not in the sequence (e.g., from a random trial),
                    # the probability remains 'L'
                    probability_type = 'L'
    
        # Override for the first two trials of the block
        if trial_in_block_num <= 2:
            probability_type = 'X'

        # --- Calculate Onset Trigger based on Type and Probability ---
        if trial_type == 'P':
            trial_trigger = 50
        elif trial_type == 'R':
            if probability_type == 'H':
                trial_trigger = 61
            elif probability_type == 'L':
                trial_trigger = 62
            elif probability_type == 'T':
                trial_trigger = 63
            elif probability_type == 'R':
                trial_trigger = 64
            elif probability_type == 'X':
                trial_trigger = 65

        # Update the positions of the last two trials
        pos_minus_2 = pos_minus_1
        pos_minus_1 = target_stim_pos

        target_stim_index = target_stim_pos - 1
    
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
            image=target_image_path,
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
        response_timer = core.Clock()
    
        correct_response_given = False
        while not correct_response_given:
            if 'escape' in event.getKeys():
                break
        
            for stim_dict in stimuli:
                stim_dict['stim'].draw()
            border_circle.draw()
            target_image.draw()
            win.flip()
        
            response_keys = event.getKeys(keyList=keys + ['escape'])
        
            if response_keys:
                pressed_key = response_keys[0]
            
                if pressed_key == 'escape':
                    break
            
                rt_non_cumulative = response_timer.getTime()
                rt_cumulative = cumulative_timer.getTime()
            
                was_correct = (pressed_key == stimuli[target_stim_index]['key'])
                pressed_key_pos = keys.index(pressed_key) + 1
            
                if was_correct:
                    response_trigger = response_type_base + pressed_key_pos
                else:
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
                    'trial_in_block_num': trial_in_block + 1,
                    'trial_type': trial_type,
                    'probability_type': probability_type,
                    'sequence_used': sequence_to_save_current,
                    'stimulus_position_num': target_stim_pos,
                    'rt_non_cumulative_s': rt_non_cumulative,
                    'rt_cumulative_s': rt_cumulative,
                    'correct_key_pressed': stimuli[target_stim_index]['key'],
                    'response_key_pressed': pressed_key,
                    'correct_response': was_correct,
                    'epoch': epoch
                })
            
                response_timer.reset()

                if was_correct:
                    correct_response_given = True
        
        if 'escape' in event.getKeys():
            break
    
    # --- Display feedback for 3 seconds ---
    correct_rts = [d['rt_cumulative_s'] for d in block_data if d['correct_response']]
    total_correct_responses = sum(1 for d in block_data if d['correct_response'])
    total_responses = len(block_data)

    mean_rt = np.mean(correct_rts) if correct_rts else 0
    accuracy = (total_correct_responses / total_responses) * 100 if total_responses > 0 else 0
    
    # Determine the performance message and color
    if accuracy < 90:
        performance_message = "Please try to be more accurate."
        performance_color = 'red'
    elif mean_rt > 0.350:
        performance_message = "Please try to be faster."
        performance_color = 'red'
    else:
        performance_message = "Good job."
        performance_color = 'green'

    # Create separate TextStim objects for each part of the feedback
    feedback_header_text = f"End of block {block_num} feedback:"
    feedback_stats_text = f"Mean RT: {mean_rt:.2f} s\nAccuracy: {accuracy:.2f} %"
    
    feedback_header = visual.TextStim(win, text=feedback_header_text, color='black', height=40, pos=(0, 100), wrapWidth=1000)
    feedback_stats = visual.TextStim(win, text=feedback_stats_text, color='black', height=30, pos=(0, 0), wrapWidth=1000)
    feedback_performance = visual.TextStim(win, text=performance_message, color=performance_color, height=40, pos=(0, -100), wrapWidth=1000)
    
    # Draw all three stimuli before the flip
    win.flip()
    feedback_header.draw()
    feedback_stats.draw()
    feedback_performance.draw()

    if p_port:
        p_port.setData(20 + block_num)
        core.wait(0.01)
        p_port.setData(0)
    else:
        print(f"Faking parallel port trigger: {20 + block_num}")

    win.flip()
    core.wait(3) # Wait for 3 seconds

    # --- Display continuation message on a separate screen ---
    if block_num < NUM_BLOCKS:
        continuation_text = "Press any key to start the next block."
        continuation_message = visual.TextStim(win, text=continuation_text, color='black', height=40, wrapWidth=1000)
        
        win.flip()
        continuation_message.draw()
        win.flip()

        event.waitKeys()
        if p_port:
            p_port.setData(10 + (block_num + 1))
            core.wait(0.01)
            p_port.setData(0)
        else:
            print(f"Faking parallel port trigger: {10 + (block_num + 1)}")

    # Append block data to all_data for cumulative saving
    all_data.extend(block_data)
    
    # --- Save data after each block ---
    data_folder = 'data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    
    filename = os.path.join(data_folder, f"participant_{expInfo['participant']}_session_{expInfo['session']}_data.csv")
    
    # Write all data collected so far to the file
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'probability_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'epoch']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Data for Block {block_num} saved successfully.")

# --- End of Experiment message ---
end_text = "End of experiment. Press any key to exit."
end_message = visual.TextStim(win, text=end_text, color='black', height=40, wrapWidth=1000)
end_message.draw()
win.flip()
event.waitKeys()

win.close()
core.quit()