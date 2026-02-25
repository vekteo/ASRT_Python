######################################################################################################

# Created by Teodóra Vékony (Gran Canaria Cognitive Research Center, Universidad del Atlántico Medio)
# email: teodora.vekony@pdi.atlanticomedio.es
# gccognitive.es
# teodoravekony.com
# github.com/vekteo

######################################################################################################

from psychopy import visual, core, event, gui
from psychopy.hardware import keyboard
import random
import csv
import configparser
import numpy as np
import os
import io
import struct
import sys
from datetime import datetime
from nogo_logic import select_nogo_trials_in_block
from mind_wandering import show_mind_wandering_probe
from config_helpers import get_text_with_newlines, set_global_text_config
import serial
import experiment_utils as utils
from mw_instructions import show_mw_instructions_and_quiz
import gc

# --- GUI for Participant Info ---
expInfo = {'participant': '1', 'session': '1', 'language': ['es', 'en', 'hu']}
dlg = gui.DlgFromDict(dictionary=expInfo, title='Experiment Settings')
if not dlg.OK:
    core.quit()

# --- Generate unique filename ---
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
data_folder = 'data'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)
unique_filename = os.path.join(
    data_folder,
    f"participant_{expInfo['participant']}_session_{expInfo['session']}_{timestamp_str}_data.csv"
)

# --- START LOGGING HERE ---
log_filename = unique_filename.replace('.csv', '_console_log.txt')
print(f"Redirecting output to: {log_filename}")

original_stdout = sys.stdout
sys.stdout = utils.LogTee(log_filename, original_stdout)

# --- Define Fieldnames for CSV ---
fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'triplet_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'is_nogo', 'is_practice', 'epoch', 'is_first_response', 
              'mind_wandering_rating_1', 'mind_wandering_rating_2', 'mind_wandering_rating_3', 'mind_wandering_rating_4']

# --- Write initial CSV Header ---
try:
    with open(unique_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    print(f"Data file initialized: {unique_filename}")
except Exception as e:
    print(f"ERROR: Failed to write initial CSV header: {e}")
    core.quit()

# --- Load experiment settings ---
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
    MANDATORY_WAIT = config.getfloat('Experiment', 'mandatory_wait_before_next_block_s', fallback=0.0)    
    ISI_DURATION = config.getfloat('Experiment', 'isi_duration_s')
    NOGO_TRIAL_DURATION = config.getfloat('Experiment', 'nogo_trial_duration_s')
    FEEDBACK_ENABLED = config.getboolean('Experiment', 'feedback_enabled')
    
    KEYS_STR = config.get('Experiment', 'response_keys_list')
    keys = [k.strip() for k in KEYS_STR.split(',')]
    target_image_path = config.get('Experiment', 'target_image_filename')
    nogo_image_path = config.get('Experiment', 'nogo_image_filename')
    BACKGROUND_COLOR = config.get('Experiment', 'background_color', fallback='white')
    FOREGROUND_COLOR = config.get('Experiment', 'foreground_color', fallback='black')

    if len(keys) != 4:
        print("Error: The 'response_keys_list' in settings must contain exactly 4 keys.")
        core.quit()
        
    RIPONDA_ENABLED = config.getboolean('Experiment', 'riponda_enabled', fallback=False)
    RIPONDA_PORT_NAME = config.get('Experiment', 'riponda_port', fallback='COM3')
    RIPONDA_BAUDRATE = config.getint('Experiment', 'riponda_baudrate', fallback=115200)
      
except (configparser.Error, FileNotFoundError) as e:
    print(f"Error reading configuration file: {e}")
    core.quit()

# --- Load experiment text ---
language_code = expInfo['language']
text_filename = f'language/experiment_text_{language_code}.ini'
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
        raise FileNotFoundError(f"Text file '{text_filename}' is empty.")
except Exception as e:
    print(f"Error loading experiment text file: {e}")
    core.quit()

set_global_text_config(text_config)

# --- Define sequences ---
all_sequences = [
    [1, 2, 3, 4], [1, 2, 4, 3], [1, 3, 2, 4],
    [1, 3, 4, 2], [1, 4, 3, 2], [1, 4, 2, 3],
    [2, 1, 3, 4], [2, 1, 4, 3], [2, 3, 1, 4],
    [2, 3, 4, 1], [2, 4, 1, 3], [2, 4, 3, 1],
    [3, 1, 2, 4], [3, 1, 4, 2], [3, 2, 1, 4],
    [3, 2, 4, 1], [3, 4, 2, 1], [3, 4, 1, 2],
    [4, 1, 2, 3], [4, 1, 3, 2], [4, 2, 1, 3],
    [4, 2, 3, 1], [4, 3, 1, 2], [4, 3, 2, 1]
]
participant_num = int(expInfo['participant'])
sequence_index = (participant_num - 1) % len(all_sequences)
pattern_sequence = all_sequences[sequence_index]
sequence_to_save = str(pattern_sequence).replace('[', '').replace(']', '').replace(' ', '')

# --- Setup window and stimuli ---
win = visual.Window(
    size=[1920, 1080], 
    fullscr=True, 
    monitor="testMonitor",
    units="pix", 
    color=BACKGROUND_COLOR, 
    multiSample=True, 
    numSamples=16,
    waitBlanking=True 
)
kb = keyboard.Keyboard()
circle_radius = 60
y_pos = 0.0
x_positions = [-240, -80, 80, 240]

stimuli = []
for x, key in zip(x_positions, keys):
    circle = visual.Circle(win=win, radius=circle_radius, fillColor='white', lineColor=FOREGROUND_COLOR, lineWidth=3, pos=(x, y_pos))
    stimuli.append({'stim': circle, 'key': key})

image_size = circle_radius * 2 - 3
border_circles = []
image_stims = []
fixation_cross = visual.TextStim(win, text='+', color=FOREGROUND_COLOR, height=50, font='Arial')
for s in stimuli:
    border = visual.Circle(win=win, radius=circle_radius, fillColor='white', pos=s['stim'].pos)
    border_circles.append(border)
    img = visual.ImageStim(win=win, image=target_image_path, size=image_size, pos=s['stim'].pos, interpolate=True)
    image_stims.append(img)

feedback_header = visual.TextStim(win, text='', color=FOREGROUND_COLOR, height=40, pos=(0, 100), wrapWidth=1600, font='Arial')
feedback_stats = visual.TextStim(win, text='', color=FOREGROUND_COLOR, height=30, pos=(0, 0), wrapWidth=1600, font='Arial')
feedback_performance = visual.TextStim(win, text='', color='green', height=40, pos=(0, -100), wrapWidth=1600, font='Arial')

# --- Riponda Byte Map ---
riponda_byte_map = {48: keys[0], 112: keys[1], 176: keys[2], 240: keys[3]}

# --- Initialize serial ports ---
ser_port = None
COM_PORT_NAME = 'COM3'
try:
    ser_port = serial.Serial(port=COM_PORT_NAME, baudrate=115200, timeout=1)
    ser_port.reset_input_buffer()
    ser_port.reset_output_buffer()
    ser_port.write(bytes([0]))
    ser_port.flush()
except Exception as e:
    print(f"Serial port {COM_PORT_NAME} not found: {e}")
    ser_port = None

riponda_port = None
if RIPONDA_ENABLED:
    try:
        riponda_port = serial.Serial(port=RIPONDA_PORT_NAME, baudrate=RIPONDA_BAUDRATE, timeout=0)
        riponda_port.reset_input_buffer()
    except Exception as e:
        print(f"Riponda port {RIPONDA_PORT_NAME} not found: {e}")
        riponda_port = None

# --- Helper Functions ---
def quit_experiment():
    if ser_port:
        try:
            ser_port.close()
        except Exception:
            pass
    if riponda_port:
        try:
            riponda_port.close()
        except Exception:
            pass
    if win:
        try:
            win.close()
        except Exception:
            pass
    
    if hasattr(sys.stdout, 'close'):
        sys.stdout.close()
    
    core.quit()

def wait_for_response():
    kb.clearEvents()
    if riponda_port:
        try:
            riponda_port.reset_input_buffer()
        except Exception:
            pass
    
    input_received = False
    while not input_received:
        keys_pressed = kb.getKeys(waitRelease=False)
        if keys_pressed:
            if 'escape' in [k.name for k in keys_pressed]:
                quit_experiment()
            input_received = True
            
        if not input_received and riponda_port and riponda_port.in_waiting >= 6:
            try:
                packet = riponda_port.read(6)
                if len(packet) == 6 and packet[0] == 0x6b:
                    input_received = True
                elif len(packet) == 6:
                    riponda_port.reset_input_buffer()
            except Exception:
                try:
                    riponda_port.reset_input_buffer()
                except Exception:
                    pass
    core.wait(0.5)

# --- Instructions ---
instruction_text = get_text_with_newlines('Instructions', 'welcome_screen').format(keys_list=", ".join([f"'{k}'" for k in keys]))
instruction_message = visual.TextStim(win, text=instruction_text, color=FOREGROUND_COLOR, height=30, wrapWidth=1600, font='Arial')
instruction_message.draw()
win.flip()
wait_for_response()

# --- No-Go instructions ---
if NO_GO_TRIALS_ENABLED:
    try:
        nogo_inst_text = get_text_with_newlines('Instructions', 'nogo_screen')
    except:
        nogo_inst_text = "Attention:\n\nPress buttons for DOG, do NOT press for CAT.\n\nPress any button to continue."
    nogo_message = visual.TextStim(win, text=nogo_inst_text, color=FOREGROUND_COLOR, height=30, wrapWidth=1600, font='Arial')
    nogo_message.draw()
    win.flip()
    wait_for_response()

# --- MW Instructions & Quiz ---
if MW_TESTING_INVOLVED:
    show_mw_instructions_and_quiz(
        win, 
        quit_experiment, 
        RUN_COMPREHENSION_QUIZ, 
        text_filename, 
        riponda_port=riponda_port,
        fg_color=FOREGROUND_COLOR,
        bg_color=BACKGROUND_COLOR
    )

# --- Start Experiment Screen ---
if PRACTICE_ENABLED:
    start_text = get_text_with_newlines('Screens', 'start_practice').format(NUM_PRACTICE_BLOCKS=NUM_PRACTICE_BLOCKS)
    start_trigger_value = 90
else:
    start_text = get_text_with_newlines('Screens', 'start_main')
    start_trigger_value = 1
start_message = visual.TextStim(win, text=start_text, color=FOREGROUND_COLOR, height=40, wrapWidth=1600, font='Arial')
start_message.draw()
win.flip()

key_pressed = kb.waitKeys(keyList=['space', 'escape'])
if 'escape' in [k.name for k in key_pressed]:
    quit_experiment()

utils.send_trigger_pulse(ser_port, start_trigger_value)

# --- Countdown ---
prep_text = get_text_with_newlines('Screens', 'countdown_message')
prep_message = visual.TextStim(win, text=prep_text, color=FOREGROUND_COLOR, height=40, wrapWidth=1600, font='Arial')
prep_message.draw()
win.flip()
utils.send_trigger_pulse(ser_port, 180)
core.wait(10.0)

# --- State variables ---
total_trial_count = 0
NA_MW_RATING = 'NA'

# --- Practice Loop ---
for practice_block_num in range(1, NUM_PRACTICE_BLOCKS + 1) if PRACTICE_ENABLED else []:
    block_data = []
    
    nogo_trial_indices_in_block = set()
    if NO_GO_TRIALS_ENABLED:
        pre_block_trials = []
        for trial_in_block in range(TRIALS_PER_BLOCK):
            pre_block_trials.append({'trial_in_block_num': trial_in_block + 1, 'trial_type': 'R'})
        try:
            nogo_indices = select_nogo_trials_in_block(range(len(pre_block_trials)), pre_block_trials, 0, NUM_NO_GO_TRIALS)
            nogo_trial_indices_in_block.update(nogo_indices)
        except Exception as e:
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
        kb.clearEvents()
        if riponda_port: 
             riponda_port.reset_input_buffer()

        trial_in_block_num = trial_in_block + 1
        is_nogo = (trial_in_block in nogo_trial_indices_in_block)

        for stim_dict in stimuli:
            stim_dict['stim'].fillColor = 'white' 
            stim_dict['stim'].draw()
        win.flip()
        core.wait(ISI_DURATION)

        target_stim_pos = practice_positions_list[practice_list_index]
        practice_list_index += 1
        trial_type = 'R'
        triplet_type = 'X'
        
        target_stim_index = target_stim_pos - 1
        image_path_to_use = nogo_image_path if is_nogo else target_image_path
            
        stimuli[target_stim_index]['stim'].fillColor = 'blue'
        border = border_circles[target_stim_index]
        target_image = image_stims[target_stim_index]
        target_image.image = image_path_to_use
        target_image.pos = stimuli[target_stim_index]['stim'].pos
        
        for stim_dict in stimuli:
            stim_dict['stim'].draw()
        border.draw()
        target_image.draw()
        
        # --- PRECISE ONSET ---
        onset_time = win.flip() 
        utils.send_trigger_pulse(ser_port, (251 if is_nogo else 151) + target_stim_pos)

        if is_nogo:
            response_logged = False
            while (core.getTime() - onset_time) < NOGO_TRIAL_DURATION:
                responses = kb.getKeys(keyList=keys + ['escape'], waitRelease=False)
                if not responses and riponda_port and riponda_port.in_waiting >= 6: 
                    try:
                        packet = riponda_port.read(6)
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            rt_now = core.getTime() - onset_time
                            responses = [type('obj', (object,), {'name': riponda_byte_map[packet[1]], 'rt': rt_now})()]
                    except Exception: pass
                
                if responses and not response_logged:
                    resp = responses[0]
                    if resp.name == 'escape': quit_experiment()
                    rt_val = resp.rt if hasattr(resp, 'rt') else core.getTime() - onset_time
                    utils.send_trigger_pulse(ser_port, 91 + keys.index(resp.name) + 1)
                    block_data.append({
                        'participant': expInfo['participant'], 'session': expInfo['session'], 'block_number': practice_block_num, 'trial_number': total_trial_count, 'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type, 'triplet_type': triplet_type, 'sequence_used': sequence_to_save, 'stimulus_position_num': target_stim_pos, 'rt_non_cumulative_s': rt_val, 'rt_cumulative_s': rt_val, 'correct_key_pressed': 'NoGo', 'response_key_pressed': resp.name, 'correct_response': False, 'is_nogo': True, 'is_practice': True, 'epoch': 0, 'is_first_response': 1, 'mind_wandering_rating_1': na_ratings[0], 'mind_wandering_rating_2': na_ratings[1], 'mind_wandering_rating_3': na_ratings[2], 'mind_wandering_rating_4': na_ratings[3]
                    })
                    response_logged = True
            if not response_logged:
                block_data.append({
                    'participant': expInfo['participant'], 'session': expInfo['session'], 'block_number': practice_block_num, 'trial_number': total_trial_count, 'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type, 'triplet_type': triplet_type, 'sequence_used': sequence_to_save, 'stimulus_position_num': target_stim_pos, 'rt_non_cumulative_s': None, 'rt_cumulative_s': None, 'correct_key_pressed': 'NoGo', 'response_key_pressed': 'None', 'correct_response': True, 'is_nogo': True, 'is_practice': True, 'epoch': 0, 'is_first_response': 1, 'mind_wandering_rating_1': na_ratings[0], 'mind_wandering_rating_2': na_ratings[1], 'mind_wandering_rating_3': na_ratings[2], 'mind_wandering_rating_4': na_ratings[3]
                })
        else:
            correct_response_given = False
            first_attempt_in_trial = True
            time_of_last_response = 0.0
            while not correct_response_given:
                res_obj = None
                kb_res = kb.getKeys(keyList=keys + ['escape'], waitRelease=False)
                if kb_res:
                    rt_now = core.getTime() - onset_time
                    res_obj = type('obj', (object,), {'name': kb_res[0].name, 'rt': rt_now})()
                elif riponda_port and riponda_port.in_waiting >= 6:
                    try:
                        packet = riponda_port.read(6) 
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            rt_now = core.getTime() - onset_time
                            res_obj = type('obj', (object,), {'name': riponda_byte_map[packet[1]], 'rt': rt_now})()
                    except Exception: pass
                
                if res_obj:
                    if res_obj.name == 'escape': quit_experiment()
                    rt_cumulative = res_obj.rt
                    rt_non_cumulative = rt_cumulative - time_of_last_response
                    was_correct = (res_obj.name == stimuli[target_stim_index]['key'])
                    utils.send_trigger_pulse(ser_port, (71 if was_correct else 81) + keys.index(res_obj.name) + 1)
                    block_data.append({
                        'participant': expInfo['participant'], 'session': expInfo['session'], 'block_number': practice_block_num, 'trial_number': total_trial_count, 'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type, 'triplet_type': triplet_type, 'sequence_used': sequence_to_save, 'stimulus_position_num': target_stim_pos, 'rt_non_cumulative_s': rt_non_cumulative, 'rt_cumulative_s': rt_cumulative, 'correct_key_pressed': stimuli[target_stim_index]['key'], 'response_key_pressed': res_obj.name, 'correct_response': was_correct, 'is_nogo': False, 'is_practice': True, 'epoch': 0, 'is_first_response': 1 if first_attempt_in_trial else 0, 'mind_wandering_rating_1': na_ratings[0], 'mind_wandering_rating_2': na_ratings[1], 'mind_wandering_rating_3': na_ratings[2], 'mind_wandering_rating_4': na_ratings[3]
                    })
                    first_attempt_in_trial = False
                    time_of_last_response = rt_cumulative
                    if was_correct: correct_response_given = True

    mw_ratings = show_mind_wandering_probe(win, ser_port, MW_TESTING_INVOLVED, NA_MW_RATING, quit_experiment, riponda_port=riponda_port, fg_color=FOREGROUND_COLOR, bg_color=BACKGROUND_COLOR)
    for d in block_data: d.update({'mind_wandering_rating_1': mw_ratings[0], 'mind_wandering_rating_2': mw_ratings[1], 'mind_wandering_rating_3': mw_ratings[2], 'mind_wandering_rating_4': mw_ratings[3]})
    try:
        with open(unique_filename, 'a', newline='') as csvfile: csv.DictWriter(csvfile, fieldnames=fieldnames).writerows(block_data)
    except: pass

    if FEEDBACK_ENABLED:
        correct_rts = [d['rt_cumulative_s'] for d in block_data if d['correct_response'] and not d['is_nogo']]
        total_correct = sum(1 for d in block_data if d['correct_response'] and not d['is_nogo'])
        total_go = len([d for d in block_data if not d['is_nogo']])
        mean_rt = np.mean(correct_rts) if correct_rts else 0
        accuracy = (total_correct / total_go) * 100 if total_go > 0 else 0
        feedback_header.text = get_text_with_newlines('Screens', 'feedback_header').format(block_num=practice_block_num)
        feedback_stats.text = f"Mean RT: {mean_rt:.2f} s\nAccuracy: {accuracy:.2f} %"
        if accuracy < 90: feedback_performance.text, feedback_performance.color = get_text_with_newlines('Screens', 'feedback_accurate'), 'red'
        elif mean_rt > 0.350: feedback_performance.text, feedback_performance.color = get_text_with_newlines('Screens', 'feedback_faster'), 'red'
        else: feedback_performance.text, feedback_performance.color = get_text_with_newlines('Screens', 'feedback_good_job'), 'green'
        feedback_header.draw(); 
        feedback_stats.draw(); 
        feedback_performance.draw(); 
        win.flip(); 
        core.wait(3)
    
    gc.collect() 
    if practice_block_num < NUM_PRACTICE_BLOCKS:
        if MANDATORY_WAIT > 0: 
            fixation_cross.draw(); 
            win.flip(); 
            core.wait(MANDATORY_WAIT)
        visual.TextStim(win, text=get_text_with_newlines('Screens', 'next_practice'), color=FOREGROUND_COLOR, height=40, wrapWidth=1600, font='Arial').draw(); win.flip(); wait_for_response(); utils.send_trigger_pulse(ser_port, 98)

if PRACTICE_ENABLED:
    visual.TextStim(win, text=get_text_with_newlines('Screens', 'end_practice'), color=FOREGROUND_COLOR, height=40, wrapWidth=1600, font='Arial').draw(); win.flip(); wait_for_response(); utils.send_trigger_pulse(ser_port, 99)

# --- Main Experiment Loop ---
for block_num in range(1, NUM_BLOCKS + 1):
    block_data = []; pattern_index = 0; pos_minus_1 = None; pos_minus_2 = None; current_pattern_sequence = list(pattern_sequence); random_list_index = 0
    epoch = ((block_num - 1) // 5) + 1
    if INTERFERENCE_EPOCH_ENABLED and epoch == INTERFERENCE_EPOCH_NUM:
        if current_pattern_sequence == list(pattern_sequence): current_pattern_sequence.reverse()
    elif current_pattern_sequence != list(pattern_sequence) and epoch != INTERFERENCE_EPOCH_NUM:
        current_pattern_sequence = list(pattern_sequence)
    
    num_random_trials = TRIALS_PER_BLOCK - (TRIALS_PER_BLOCK // 2)
    random_positions_list = []
    positions_per_stim = num_random_trials // len(stimuli)
    for pos_num in range(1, len(stimuli) + 1): random_positions_list.extend([pos_num] * positions_per_stim)
    random.shuffle(random_positions_list)
    
    nogo_trial_indices_in_block = set()
    if NO_GO_TRIALS_ENABLED:
        pre_block_trials = []
        for trial_in_block in range(TRIALS_PER_BLOCK):
            pre_block_trials.append({'trial_in_block_num': trial_in_block + 1, 'trial_type': 'P' if (trial_in_block + 1) % 2 == 0 else 'R'})
        try:
            nogo_indices = select_nogo_trials_in_block(range(len(pre_block_trials)), pre_block_trials, NUM_NO_GO_TRIALS // 2, NUM_NO_GO_TRIALS - (NUM_NO_GO_TRIALS // 2))
            nogo_trial_indices_in_block.update(nogo_indices)
        except: core.quit()

    for trial_in_block in range(TRIALS_PER_BLOCK):
        total_trial_count += 1; trial_in_block_num = trial_in_block + 1; is_nogo = (trial_in_block in nogo_trial_indices_in_block)
        
        if riponda_port: riponda_port.reset_input_buffer()
        kb.clearEvents()
        
        for stim_dict in stimuli: 
            stim_dict['stim'].fillColor = 'white'
            stim_dict['stim'].draw()
        win.flip(); 
        core.wait(ISI_DURATION)

        if trial_in_block_num % 2 == 0:
            target_stim_pos = current_pattern_sequence[pattern_index]; pattern_index = (pattern_index + 1) % len(current_pattern_sequence); trial_type = 'P'
        else:
            target_stim_pos = random_positions_list[random_list_index]; random_list_index += 1; trial_type = 'R'

        triplet_type = 'L'
        if trial_type == 'P': triplet_type = 'H'
        elif pos_minus_2 is not None:
            try:
                cur_idx = current_pattern_sequence.index(target_stim_pos)
                if pos_minus_2 == current_pattern_sequence[(cur_idx - 1) % len(current_pattern_sequence)]: triplet_type = 'H'
                elif pos_minus_2 == target_stim_pos:
                    triplet_type = 'T'
                    if pos_minus_1 == target_stim_pos: triplet_type = 'R'
            except: pass
        if trial_in_block_num <= 2: triplet_type = 'X'
        
        trigger_offset = (200 if is_nogo else 100)
        if trial_type == 'P' and triplet_type == 'H': trial_trigger = trigger_offset + 1 + target_stim_pos
        elif trial_type == 'R' and triplet_type == 'H': trial_trigger = trigger_offset + 11 + target_stim_pos
        elif triplet_type == 'L': trial_trigger = trigger_offset + 21 + target_stim_pos
        elif triplet_type == 'T': trial_trigger = trigger_offset + 31 + target_stim_pos
        elif triplet_type == 'R': trial_trigger = trigger_offset + 41 + target_stim_pos
        else: trial_trigger = trigger_offset + 51 + target_stim_pos

        pos_minus_2, pos_minus_1 = pos_minus_1, target_stim_pos
        target_stim_index = target_stim_pos - 1
        stimuli[target_stim_index]['stim'].fillColor = 'blue'
        target_image = image_stims[target_stim_index]
        target_image.image = nogo_image_path if is_nogo else target_image_path
        target_image.pos = stimuli[target_stim_index]['stim'].pos
        
        for stim_dict in stimuli: stim_dict['stim'].draw()
        border_circles[target_stim_index].draw(); 
        target_image.draw()
        
        onset_time = win.flip()
        utils.send_trigger_pulse(ser_port, trial_trigger)

        if is_nogo:
            response_logged = False
            while (core.getTime() - onset_time) < NOGO_TRIAL_DURATION:
                responses = kb.getKeys(keyList=keys + ['escape'], waitRelease=False)
                if not responses and riponda_port and riponda_port.in_waiting >= 6:
                    try:
                        packet = riponda_port.read(6)
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            rt_now = core.getTime() - onset_time
                            responses = [type('obj', (object,), {'name': riponda_byte_map[packet[1]], 'rt': rt_now})()]
                    except: pass
                    
                if responses and not response_logged:
                    resp = responses[0]
                    if resp.name == 'escape': quit_experiment()
                    rt_val = resp.rt if hasattr(resp, 'rt') else core.getTime() - onset_time
                    utils.send_trigger_pulse(ser_port, 91 + keys.index(resp.name) + 1)
                    block_data.append({'participant': expInfo['participant'], 'session': expInfo['session'], 'block_number': block_num, 'trial_number': total_trial_count, 'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type, 'triplet_type': triplet_type, 'sequence_used': sequence_to_save, 'stimulus_position_num': target_stim_pos, 'rt_non_cumulative_s': rt_val, 'rt_cumulative_s': rt_val, 'correct_key_pressed': 'NoGo', 'response_key_pressed': resp.name, 'correct_response': False, 'is_nogo': True, 'is_practice': False, 'epoch': epoch, 'is_first_response': 1, 'mind_wandering_rating_1': NA_MW_RATING, 'mind_wandering_rating_2': NA_MW_RATING, 'mind_wandering_rating_3': NA_MW_RATING, 'mind_wandering_rating_4': NA_MW_RATING})
                    response_logged = True
            if not response_logged: block_data.append({'participant': expInfo['participant'], 'session': expInfo['session'], 'block_number': block_num, 'trial_number': total_trial_count, 'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type, 'triplet_type': triplet_type, 'sequence_used': sequence_to_save, 'stimulus_position_num': target_stim_pos, 'rt_non_cumulative_s': None, 'rt_cumulative_s': None, 'correct_key_pressed': 'NoGo', 'response_key_pressed': 'None', 'correct_response': True, 'is_nogo': True, 'is_practice': False, 'epoch': epoch, 'is_first_response': 1, 'mind_wandering_rating_1': NA_MW_RATING, 'mind_wandering_rating_2': NA_MW_RATING, 'mind_wandering_rating_3': NA_MW_RATING, 'mind_wandering_rating_4': NA_MW_RATING})
        else:
            correct_response_given = False; first_attempt_in_trial = True; time_of_last_response = 0.0
            while not correct_response_given:
                res_obj = None; kb_res = kb.getKeys(keyList=keys + ['escape'], waitRelease=False)
                if kb_res:
                    rt_now = core.getTime() - onset_time
                    res_obj = type('obj', (object,), {'name': kb_res[0].name, 'rt': rt_now})()
                elif riponda_port and riponda_port.in_waiting >= 6:
                    try:
                        packet = riponda_port.read(6)
                        if packet[0] == 0x6b and packet[1] in riponda_byte_map:
                            rt_now = core.getTime() - onset_time
                            res_obj = type('obj', (object,), {'name': riponda_byte_map[packet[1]], 'rt': rt_now})()
                    except: pass
                if res_obj:
                    if res_obj.name == 'escape': quit_experiment()
                    rt_cumulative = res_obj.rt
                    rt_non_cumulative = rt_cumulative - time_of_last_response
                    was_correct = (res_obj.name == stimuli[target_stim_index]['key'])
                    utils.send_trigger_pulse(ser_port, (71 if was_correct else 81) + keys.index(res_obj.name) + 1)
                    block_data.append({'participant': expInfo['participant'], 'session': expInfo['session'], 'block_number': block_num, 'trial_number': total_trial_count, 'trial_in_block_num': trial_in_block_num, 'trial_type': trial_type, 'triplet_type': triplet_type, 'sequence_used': sequence_to_save, 'stimulus_position_num': target_stim_pos, 'rt_non_cumulative_s': rt_non_cumulative, 'rt_cumulative_s': rt_cumulative, 'correct_key_pressed': stimuli[target_stim_index]['key'], 'response_key_pressed': res_obj.name, 'correct_response': was_correct, 'is_nogo': False, 'is_practice': False, 'epoch': epoch, 'is_first_response': 1 if first_attempt_in_trial else 0, 'mind_wandering_rating_1': NA_MW_RATING, 'mind_wandering_rating_2': NA_MW_RATING, 'mind_wandering_rating_3': NA_MW_RATING, 'mind_wandering_rating_4': NA_MW_RATING})
                    first_attempt_in_trial = False
                    time_of_last_response = rt_cumulative
                    if was_correct: correct_response_given = True

    mw_ratings = show_mind_wandering_probe(win, ser_port, MW_TESTING_INVOLVED, NA_MW_RATING, quit_experiment, riponda_port=riponda_port, fg_color=FOREGROUND_COLOR, bg_color=BACKGROUND_COLOR)
    for d in block_data: d.update({'mind_wandering_rating_1': mw_ratings[0], 'mind_wandering_rating_2': mw_ratings[1], 'mind_wandering_rating_3': mw_ratings[2], 'mind_wandering_rating_4': mw_ratings[3]})
    try:
        with open(unique_filename, 'a', newline='') as csvfile: csv.DictWriter(csvfile, fieldnames=fieldnames).writerows(block_data)
    except: pass

    if FEEDBACK_ENABLED:
        correct_rts = [d['rt_cumulative_s'] for d in block_data if d['correct_response'] and not d['is_nogo']]
        total_correct = sum(1 for d in block_data if d['correct_response'] and not d['is_nogo'])
        total_go = len([d for d in block_data if not d['is_nogo']])
        mean_rt = np.mean(correct_rts) if correct_rts else 0
        accuracy = (total_correct / total_go) * 100 if total_go > 0 else 0
        feedback_header.text = get_text_with_newlines('Screens', 'feedback_header').format(block_num=block_num)
        rt_label = get_text_with_newlines('Screens', 'feedback_rt')
        acc_label = get_text_with_newlines('Screens', 'feedback_acc')
        feedback_stats.text = f"{rt_label} {mean_rt:.2f} s\n{acc_label} {accuracy:.2f} %"        
        if accuracy < 90: 
            feedback_performance.text, feedback_performance.color = get_text_with_newlines('Screens', 'feedback_accurate'), 'red'
        elif mean_rt > 0.350: 
            feedback_performance.text, feedback_performance.color = get_text_with_newlines('Screens', 'feedback_faster'), 'red'
        else: 
            feedback_performance.text, feedback_performance.color = get_text_with_newlines('Screens', 'feedback_good_job'), 'green'
        feedback_header.draw(); 
        feedback_stats.draw(); 
        feedback_performance.draw(); 
        win.flip(); 
        core.wait(3)

    if block_num < NUM_BLOCKS:
        if MANDATORY_WAIT > 0: fixation_cross.draw(); win.flip(); core.wait(MANDATORY_WAIT)
        visual.TextStim(win, text=get_text_with_newlines('Screens', 'next_main'), color=FOREGROUND_COLOR, height=40, wrapWidth=1600, font='Arial').draw(); 
        win.flip(); 
        wait_for_response(); 
        utils.send_trigger_pulse(ser_port, 0 + (block_num + 1))
    gc.collect() 

visual.TextStim(win, text=get_text_with_newlines('Screens', 'end_experiment'), color=FOREGROUND_COLOR, height=40, wrapWidth=1600, font='Arial').draw(); 
win.flip(); 
wait_for_response(); 
quit_experiment()