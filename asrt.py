# Import the necessary PsychoPy libraries and other modules
from psychopy import visual, core, event, gui
import random
import csv
import configparser
import numpy as np
import os
import io
from datetime import datetime
from nogo_logic import select_nogo_trials_in_block
from mind_wandering import show_mind_wandering_probe
from config_helpers import get_text_with_newlines, set_global_text_config
import serial 
import experiment_utils as utils 
from mw_instructions import show_mw_instructions_and_quiz 

# --- GUI for Participant Info ---
expInfo = {'participant': '1', 'session': '1', 'language': ['en', 'es']}
dlg = gui.DlgFromDict(dictionary=expInfo, title='Experiment Settings')
if not dlg.OK:
    core.quit()

# --- Generate a unique filename with timestamp ---
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
data_folder = 'data'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

unique_filename = os.path.join(
    data_folder,
    f"participant_{expInfo['participant']}_session_{expInfo['session']}_{timestamp_str}_data.csv"
)

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
    RUN_COMPREHENSION_QUIZ = config.getboolean('Experiment', 'run_quiz_if_mw_enabled')
    PRACTICE_ENABLED = config.getboolean('Practice', 'practice_enabled')
    NUM_PRACTICE_BLOCKS = config.getint('Practice', 'num_practice_blocks')
    
    ISI_DURATION = config.getfloat('Experiment', 'isi_duration_s')
    NOGO_TRIAL_DURATION = config.getfloat('Experiment', 'nogo_trial_duration_s')
    FEEDBACK_ENABLED = config.getboolean('Experiment', 'feedback_enabled')
    
    KEYS_STR = config.get('Experiment', 'response_keys_list')
    keys = [k.strip() for k in KEYS_STR.split(',')] 
    target_image_path = config.get('Experiment', 'target_image_filename')
    nogo_image_path = config.get('Experiment', 'nogo_image_filename')

    if len(keys) != 4:
        print("Error: The 'response_keys_list' in settings must contain exactly 4 keys (comma-separated).")
        core.quit()
        
    RIPONDA_ENABLED = config.getboolean('Experiment', 'riponda_enabled', fallback=False)
    RIPONDA_PORT_NAME = config.get('Experiment', 'riponda_port', fallback='COM4')
    RIPONDA_BAUDRATE = config.getint('Experiment', 'riponda_baudrate', fallback=115200)
      
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

    with io.open(text_filename, mode='r', encoding='utf-8-sig') as f:
        file_content = f.read()
    
    file_content = file_content.strip()
    text_config.read_string(file_content)
    
    if not text_config.sections():
        raise FileNotFoundError(f"Text configuration file '{text_filename}' is empty.")
except Exception as e:
    print(f"Error loading experiment text file: {e}")
    core.quit()

set_global_text_config(text_config)

# --- Define a list of possible sequences ---
all_sequences = [
    [1, 2, 3, 4],
    [1, 2, 4, 3],
    [1, 3, 2, 4],
    [1, 3, 4, 2],
    [1, 4, 3, 2],
    [1, 4, 2, 3]
]

participant_num = int(expInfo['participant'])
sequence_index = (participant_num - 1) % len(all_sequences)
pattern_sequence = all_sequences[sequence_index]
sequence_to_save = str(pattern_sequence).replace('[', '').replace(']', '').replace(' ', '')

# --- Setup the PsychoPy window and stimuli ---
win = visual.Window(
    size=[1920, 1080],
    fullscr=True,
    monitor="testMonitor",
    units="pix",
    color='white',
    multiSample=True,
    numSamples=16
)

circle_radius = 60
y_pos = 0.0
x_positions = [-240, -80, 80, 240]

stimuli = []
for x, key in zip(x_positions, keys):
    circle = visual.Circle(
        win=win, radius=circle_radius, fillColor='white', lineColor='black', lineWidth=3, pos=(x, y_pos)
    )
    stimuli.append({'stim': circle, 'key': key})

# --- Hard-coded Riponda Byte Map ---
riponda_byte_map = {
    48: keys[0],  # Button 1
    112: keys[1], # Button 2
    176: keys[2], # Button 3
    240: keys[3]  # Button 4
}
if RIPONDA_ENABLED:
    print(f"Riponda XID byte map created: {riponda_byte_map}")

# State variables
all_data = []
total_trial_count = 0
header_written = False
NA_MW_RATING = 'NA'

# --- Initialize Serial Port for Triggers ---
ser_port = None
COM_PORT_NAME = 'COM3'

try:
    ser_port = serial.Serial(
        port=COM_PORT_NAME, baudrate=2000000, timeout=1, rtscts=False, dsrdtr=False, xonxoff=False
    )
    ser_port.reset_input_buffer()
    ser_port.reset_output_buffer()
    ser_port.write(bytes([0]))
    ser_port.flush()
    print(f"Serial port initialized at {COM_PORT_NAME} (2,000,000 baud).")
except Exception as e:
    print(f"Serial port {COM_PORT_NAME} not found or could not be initialized. Error: {e}")
    print("Continuing without serial port (triggers will be faked).")
    ser_port = None
    
riponda_port = None
if RIPONDA_ENABLED:
    try:
        riponda_port = serial.Serial(
            port=RIPONDA_PORT_NAME, baudrate=RIPONDA_BAUDRATE, timeout=0 
        )
        riponda_port.reset_input_buffer()
        print(f"Riponda response box initialized at {RIPONDA_PORT_NAME} ({RIPONDA_BAUDRATE} baud).")
    except Exception as e:
        print(f"Riponda port {RIPONDA_PORT_NAME} not found or could not be initialized. Error: {e}")
        print("Continuing with keyboard-only responses.")
        riponda_port = None
else:
    print("Riponda response box disabled in settings. Using keyboard only.")

pos_minus_1 = None
pos_minus_2 = None

# --- Helper function wrapper to save data and quit ---
def quit_experiment():
    """Wrapper function to call the utility save_and_quit."""
    print("Quitting experiment... closing ports.")
    if ser_port:
        ser_port.close()
    if riponda_port:
        riponda_port.close()
    utils.save_and_quit(win, unique_filename, all_data)

# --- HELPER FUNCTION: Wait for Riponda OR Keyboard ---
def wait_for_response():
    event.clearEvents()
    if riponda_port:
        riponda_port.reset_input_buffer()

    while True:
        # 1. Check Keyboard
        keys_pressed = event.getKeys()
        if keys_pressed:
            if 'escape' in keys_pressed:
                quit_experiment()
            return 

        # 2. Check Riponda
        if riponda_port and riponda_port.in_waiting >= 6:
            try:
                packet = riponda_port.read(6)
                if len(packet) == 6 and packet[0] == 0x6b:
                    return 
                elif len(packet) == 6:
                     riponda_port.reset_input_buffer()
            except Exception:
                riponda_port.reset_input_buffer()
        core.wait(0.01)

# --- Instruction Window ---
keys_list_str = ", ".join([f"'{k}'" for k in keys])
instruction_text = get_text_with_newlines('Instructions', 'welcome_screen').format(keys_list=keys_list_str)
instruction_message = visual.TextStim(
    win, text=instruction_text, color='black', height=30, wrapWidth=1000, alignHoriz='center', alignVert='center', font='Arial'
)
instruction_message.draw()
win.flip()
wait_for_response()

# --- No-Go Specific Instructions ---
if NO_GO_TRIALS_ENABLED:
    try:
        nogo_inst_text = get_text_with_newlines('Instructions', 'nogo_screen')
    except:
        nogo_inst_text = (
            "Attention:\n\nUsually, you will see a DOG. Press the button for the location of the dog.\n\n"
            "However, if you see a CAT, do NOT press any button.\nSimply wait for the image to disappear.\n\n"
            "Press any button to continue."
        )
    nogo_message = visual.TextStim(
        win, text=nogo_inst_text, color='black', height=30, wrapWidth=1000, alignHoriz='center', alignVert='center', font='Arial'
    )
    nogo_message.draw()
    win.flip()
    wait_for_response()

# --- Mind Wandering Probe Instructions & Quiz ---
if MW_TESTING_INVOLVED:
    show_mw_instructions_and_quiz(
        win, quit_experiment, RUN_COMPREHENSION_QUIZ, text_filename, riponda_port=riponda_port
    )
    
# --- Initial 'Start Experiment' window ---
if PRACTICE_ENABLED:
    start_text = get_text_with_newlines('Screens', 'start_practice').format(NUM_PRACTICE_BLOCKS=NUM_PRACTICE_BLOCKS)
    start_trigger_value = 90 
else:
    start_text = get_text_with_newlines('Screens', 'start_main')
    start_trigger_value = 11

start_message = visual.TextStim(win, text=start_text, color='black', height=40, wrapWidth=1000, font='Arial')
start_message.draw()
win.flip()

key_pressed = event.waitKeys(keyList=['space', 'escape'])
if 'escape' in key_pressed:
    quit_experiment()
    
utils.send_trigger_pulse(ser_port, start_trigger_value)

prep_text = get_text_with_newlines('Screens', 'countdown_message')
prep_message = visual.TextStim(win, text=prep_text, color='black', height=40, wrapWidth=1000, font='Arial')
prep_message.draw()
win.flip()
core.wait(10.0)

# --- Practice Loop ---
for practice_block_num in range(1, NUM_PRACTICE_BLOCKS + 1) if PRACTICE_ENABLED else []:
    block_data = []
    pos_minus_1 = None
    pos_minus_2 = None
    
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
    
    na_ratings = [NA_MW_RATING] * 4

    for trial_in_block in range(TRIALS_PER_BLOCK):
        total_trial_count += 1
        trial_in_block_num = trial_in_block + 1
        is_nogo = (trial_in_block in nogo_trial_indices_in_block)

        if 'escape' in event.getKeys():
            quit_experiment()

        for stim_dict in stimuli:
            stim_dict['stim'].fillColor = 'white'
            stim_dict['stim'].draw()
        win.flip()
        core.wait(ISI_DURATION)

        target_stim_pos = practice_positions_list[practice_list_index]
        practice_list_index += 1
        trial_type = 'R'
        probability_type = 'X'

        pos_minus_2 = pos_minus_1
        pos_minus_1 = target_stim_pos
        
        target_stim_index = target_stim_pos - 1
        image_path_to_use = nogo_image_path if is_nogo else target_image_path
            
        stimuli[target_stim_index]['stim'].fillColor = 'blue'
        border_circle = visual.Circle(
            win=win, radius=circle_radius, fillColor='black', pos=stimuli[target_stim_index]['stim'].pos
        )
        image_size = circle_radius * 2 - 3
        target_image = visual.ImageStim(
            win=win, image=image_path_to_use, size=image_size, pos=stimuli[target_stim_index]['stim'].pos
        )
        
        trial_trigger = (251 if is_nogo else 151) + target_stim_pos
        utils.send_trigger_pulse(ser_port, trial_trigger)
        print(f"Trial {total_trial_count} onset trigger: {trial_trigger}")

        cumulative_timer = core.Clock()
        
        if is_nogo:
            response_logged = False
            while cumulative_timer.getTime() < NOGO_TRIAL_DURATION:
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
            
                responses = None
                kb_responses = event.getKeys(keyList=keys + ['escape'], timeStamped=cumulative_timer)
                if kb_responses:
                    responses = kb_responses
                
                if not responses and riponda_port and riponda_port.in_waiting >= 6: 
                    try:
                        packet = riponda_port.read(6) 
                        rt = cumulative_timer.getTime()
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            key = riponda_byte_map[packet[1]]
                            responses = [(key, rt)]
                        riponda_port.reset_input_buffer() 
                    except Exception as e:
                        print(f"Riponda read error: {e}")
                        riponda_port.reset_input_buffer()
                
                if responses and not response_logged:
                    pressed_key, rt = responses[0]
                    if pressed_key == 'escape':
                        quit_experiment()

                    was_correct = False
                    pressed_key_pos = keys.index(pressed_key) + 1
                    response_trigger = 91 + pressed_key_pos 
                    
                    utils.send_trigger_pulse(ser_port, response_trigger)
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
                        'rt_non_cumulative_s': rt,
                        'rt_cumulative_s': rt,
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
        
        else: # Go trial
            response_timer = core.Clock()
            correct_response_given = False
            while not correct_response_given:
                if 'escape' in event.getKeys():
                    quit_experiment()
            
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
                
                pressed_key = None
                kb_keys = event.getKeys(keyList=keys + ['escape'])
                if kb_keys:
                    pressed_key = kb_keys[0]

                if not pressed_key and riponda_port and riponda_port.in_waiting >= 6: 
                    try:
                        packet = riponda_port.read(6) 
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            pressed_key = riponda_byte_map[packet[1]]
                        riponda_port.reset_input_buffer() 
                    except Exception as e:
                        print(f"Riponda read error: {e}")
                        riponda_port.reset_input_buffer()
                
                if pressed_key:
                    if pressed_key == 'escape':
                        quit_experiment()
                    rt_non_cumulative = response_timer.getTime()
                    rt_cumulative = cumulative_timer.getTime()
                
                    was_correct = (pressed_key == stimuli[target_stim_index]['key'])
                    pressed_key_pos = keys.index(pressed_key) + 1
                    
                    if was_correct:
                        response_trigger = 71 + pressed_key_pos
                    else:
                        response_trigger = 81 + pressed_key_pos
                    
                    utils.send_trigger_pulse(ser_port, response_trigger)
                    print(f"Response trigger: {response_trigger}")

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
            quit_experiment()

    # --- Mind Wandering Probe for Practice Block ---
    mw_ratings = show_mind_wandering_probe(
        win, ser_port, MW_TESTING_INVOLVED, NA_MW_RATING, quit_experiment, riponda_port=riponda_port
    )
    
    for d in block_data:
        d['mind_wandering_rating_1'] = mw_ratings[0]
        d['mind_wandering_rating_2'] = mw_ratings[1]
        d['mind_wandering_rating_3'] = mw_ratings[2]
        d['mind_wandering_rating_4'] = mw_ratings[3]

    all_data.extend(block_data)
    
    with open(unique_filename, 'w', newline='') as csvfile:
        fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'probability_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'is_nogo', 'is_practice', 'epoch', 
                      'mind_wandering_rating_1', 'mind_wandering_rating_2', 'mind_wandering_rating_3', 'mind_wandering_rating_4']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Data for Practice Block {practice_block_num} saved.")

    # --- Display feedback for 3 seconds ---
    if FEEDBACK_ENABLED:
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

        utils.send_trigger_pulse(ser_port, 161)
        win.flip()
        core.wait(3)

    if practice_block_num < NUM_PRACTICE_BLOCKS:
        continuation_text = get_text_with_newlines('Screens', 'next_practice')
        continuation_message = visual.TextStim(win, text=continuation_text, color='black', height=40, wrapWidth=1000, font='Arial')
        win.flip()
        continuation_message.draw()
        win.flip()
        
        wait_for_response()

        utils.send_trigger_pulse(ser_port, 98)
        
if PRACTICE_ENABLED:
    end_practice_text = get_text_with_newlines('Screens', 'end_practice')
    end_practice_message = visual.TextStim(win, text=end_practice_text, color='black', height=40, wrapWidth=1000, font='Arial')
    win.flip()
    end_practice_message.draw()
    win.flip()
    wait_for_response()
    utils.send_trigger_pulse(ser_port, 99)

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
    
    num_random_trials = TRIALS_PER_BLOCK - (TRIALS_PER_BLOCK // 2)

    random_positions_list = []
    positions_per_stim = num_random_trials // len(stimuli)
    for pos_num in range(1, len(stimuli) + 1):
        random_positions_list.extend([pos_num] * positions_per_stim)
    random.shuffle(random_positions_list)
    
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

    na_ratings = [NA_MW_RATING] * 4

    for trial_in_block in range(TRIALS_PER_BLOCK):
        total_trial_count += 1
        trial_in_block_num = trial_in_block + 1
        is_nogo = (trial_in_block in nogo_trial_indices_in_block)

        if 'escape' in event.getKeys():
            quit_experiment()

        for stim_dict in stimuli:
            stim_dict['stim'].fillColor = 'white'
            stim_dict['stim'].draw()
        win.flip()
        core.wait(ISI_DURATION)

        if trial_in_block_num % 2 == 0:
            target_stim_pos = current_pattern_sequence[pattern_index]
            pattern_index = (pattern_index + 1) % len(current_pattern_sequence)
            trial_type = 'P'
        else:
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
            if trial_type == 'P' and probability_type == 'H': trial_trigger = 201 + target_stim_pos
            elif trial_type == 'R' and probability_type == 'H': trial_trigger = 211 + target_stim_pos
            elif probability_type == 'L': trial_trigger = 221 + target_stim_pos
            elif probability_type == 'T': trial_trigger = 231 + target_stim_pos
            elif probability_type == 'R': trial_trigger = 241 + target_stim_pos
            elif probability_type == 'X': trial_trigger = 251 + target_stim_pos
        else:
            if trial_type == 'P': trial_trigger = 101 + target_stim_pos
            else:
                if probability_type == 'H': trial_trigger = 111 + target_stim_pos
                elif probability_type == 'L': trial_trigger = 121 + target_stim_pos
                elif probability_type == 'T': trial_trigger = 131 + target_stim_pos
                elif probability_type == 'R': trial_trigger = 141 + target_stim_pos
                elif probability_type == 'X': trial_trigger = 151 + target_stim_pos

        pos_minus_2 = pos_minus_1
        pos_minus_1 = target_stim_pos
        target_stim_index = target_stim_pos - 1
        image_path_to_use = nogo_image_path if is_nogo else target_image_path
            
        stimuli[target_stim_index]['stim'].fillColor = 'blue'
        border_circle = visual.Circle(
            win=win, radius=circle_radius, fillColor='black', pos=stimuli[target_stim_index]['stim'].pos
        )
        image_size = circle_radius * 2 - 3
        target_image = visual.ImageStim(
            win=win, image=image_path_to_use, size=image_size, pos=stimuli[target_stim_index]['stim'].pos
        )
        
        utils.send_trigger_pulse(ser_port, trial_trigger)
        print(f"Trial {total_trial_count} onset trigger: {trial_trigger}")

        cumulative_timer = core.Clock()
        
        if is_nogo:
            response_logged = False
            while cumulative_timer.getTime() < NOGO_TRIAL_DURATION:
                if 'escape' in event.getKeys():
                    quit_experiment()
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()
            
                responses = None
                kb_responses = event.getKeys(keyList=keys + ['escape'], timeStamped=cumulative_timer)
                if kb_responses:
                    responses = kb_responses
                
                if not responses and riponda_port and riponda_port.in_waiting >= 6: 
                    try:
                        packet = riponda_port.read(6) 
                        rt = cumulative_timer.getTime()
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            key = riponda_byte_map[packet[1]]
                            responses = [(key, rt)]
                        riponda_port.reset_input_buffer() 
                    except Exception as e:
                        print(f"Riponda read error: {e}")
                        riponda_port.reset_input_buffer()
                
                if responses and not response_logged:
                    pressed_key, rt = responses[0]
                    if pressed_key == 'escape':
                        quit_experiment()
                    was_correct = False
                    pressed_key_pos = keys.index(pressed_key) + 1
                    response_trigger = 91 + pressed_key_pos
                    utils.send_trigger_pulse(ser_port, response_trigger)
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
                        'rt_non_cumulative_s': rt,
                        'rt_cumulative_s': rt,
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
        
        else: # Go trial
            response_timer = core.Clock()
            correct_response_given = False
            while not correct_response_given:
                if 'escape' in event.getKeys():
                    quit_experiment()
            
                for stim_dict in stimuli:
                    stim_dict['stim'].draw()
                border_circle.draw()
                target_image.draw()
                win.flip()            
                pressed_key = None
                kb_keys = event.getKeys(keyList=keys + ['escape'])
                if kb_keys:
                    pressed_key = kb_keys[0]

                if not pressed_key and riponda_port and riponda_port.in_waiting >= 6: 
                    try:
                        packet = riponda_port.read(6)
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            pressed_key = riponda_byte_map[packet[1]]
                        riponda_port.reset_input_buffer() 
                    except Exception as e:
                        print(f"Riponda read error: {e}")
                        riponda_port.reset_input_buffer()
                
                if pressed_key:
                    if pressed_key == 'escape':
                        quit_experiment() 
                    rt_non_cumulative = response_timer.getTime()
                    rt_cumulative = cumulative_timer.getTime()
                
                    was_correct = (pressed_key == stimuli[target_stim_index]['key'])
                    pressed_key_pos = keys.index(pressed_key) + 1
                    
                    if was_correct:
                        response_trigger = 71 + pressed_key_pos
                    else:
                        response_trigger = 81 + pressed_key_pos
                    
                    utils.send_trigger_pulse(ser_port, response_trigger) 
                    print(f"Response trigger: {response_trigger}")

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
            quit_experiment()
    
    # --- Mind Wandering Probe for Main Block ---
    mw_ratings = show_mind_wandering_probe(
        win, ser_port, MW_TESTING_INVOLVED, NA_MW_RATING, quit_experiment, riponda_port=riponda_port
    ) 
    for d in block_data:
        d['mind_wandering_rating_1'] = mw_ratings[0]
        d['mind_wandering_rating_2'] = mw_ratings[1]
        d['mind_wandering_rating_3'] = mw_ratings[2]
        d['mind_wandering_rating_4'] = mw_ratings[3]

    all_data.extend(block_data)
    
    with open(unique_filename, 'w', newline='') as csvfile:
        fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'probability_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'is_nogo', 'is_practice', 'epoch', 
                      'mind_wandering_rating_1', 'mind_wandering_rating_2', 'mind_wandering_rating_3', 'mind_wandering_rating_4']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Data for Main Block {block_num} saved.")

    # --- Display feedback for 3 seconds ---
    if FEEDBACK_ENABLED:
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

        utils.send_trigger_pulse(ser_port, 160)
        win.flip()
        core.wait(3)

    if block_num < NUM_BLOCKS:
        continuation_text = get_text_with_newlines('Screens', 'next_main')
        continuation_message = visual.TextStim(win, text=continuation_text, color='black', height=40, wrapWidth=1000, font='Arial')
        win.flip()
        continuation_message.draw()
        win.flip()            
        wait_for_response()

        trigger_base = 10
        utils.send_trigger_pulse(ser_port, trigger_base + (block_num + 1))

print(f"Data saved successfully to {unique_filename}")
end_text = get_text_with_newlines('Screens', 'end_experiment')
end_message = visual.TextStim(win, text=end_text, color='black', height=40, wrapWidth=1000, font='Arial')
end_message.draw()
win.flip()
wait_for_response()

if ser_port:
    ser_port.close()
if riponda_port:
    riponda_port.close()
print("All serial ports closed.")

win.close()
core.quit()