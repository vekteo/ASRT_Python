# mw_instructions.py
# This file manages the setup and display of Mind Wandering (MW) instructions and the associated comprehension quiz.

from psychopy import visual, core, event
from config_helpers import get_text_with_newlines
import experiment_utils as utils
from quiz_logic import run_comprehension_quiz

def show_mw_instructions_and_quiz(win, quit_experiment, RUN_COMPREHENSION_QUIZ, text_filename, riponda_port=None):
    """
    Displays all Mind Wandering instruction pages and runs the
    comprehension quiz if it is enabled.
    """
    mw_riponda_map = {
        48: '1',  # Button 1 Press
        112: '2', # Button 2 Press
        176: '3', # Button 3 Press
        240: '4'  # Button 4 Press
    }

    # Q1 Response Options
    q1_button_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_1', default="Not at all"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_4', default="Completely"), 'x': 300}
    ]
    # Q2: Content of thoughts (MW-branch)
    q2_mw_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_1', default="I was thinking about nothing"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_4', default="I was thinking about something in particular"), 'x': 300}
    ]
    # Q3: Deliberateness of thoughts (MW-branch)
    q3_mw_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_1', default="I was completely spontaneous"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_4', default="I was completely deliberate"), 'x': 300}
    ]
    # Q4: Affective tone of thoughts (MW-branch)
    q4_mw_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_1', default="Completely positive"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_4', default="Completely Negative"), 'x': 300}
    ]
    # Q2: Task focus (On-Task branch)
    q2_on_task_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_on_task_label_1', default="Focus entirely on speed"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_on_task_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_on_task_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_on_task_label_4', default="Focus entirely on accuracy"), 'x': 300}
    ]
    # Q3: Concentration difficulty (On-Task branch)
    q3_on_task_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_on_task_label_1', default="Extremely difficult to concentrate"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_on_task_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_on_task_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_on_task_label_4', default="Extremely easy to concentrate"), 'x': 300}
    ]
    # Q4: Task Tiringness (On-Task branch)
    q4_on_task_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_on_task_label_1', default="Not at all tiring"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_on_task_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_on_task_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_on_task_label_4', default="Extremely tiring"), 'x': 300}
    ]
    
    # --- Mind Wandering Probe Instructions Loop ---
    mw_instruction_pages = [
        {'text_key': 'mw_intro', 'buttons_details': None},
        {'text_key': 'mw_q1', 'buttons_details': q1_button_details},
        {'text_key': 'mw_q2_off_task', 'buttons_details': q2_mw_details},
        {'text_key': 'mw_q3_spontaneous', 'buttons_details': q3_mw_details},
        {'text_key': 'mw_q4_affective', 'buttons_details': q4_mw_details},
        {'text_key': 'mw_on_task_intro', 'buttons_details': None},
        {'text_key': 'mw_q2_on_task_instr', 'buttons_details': q2_on_task_details},
        {'text_key': 'mw_q3_on_task_instr', 'buttons_details': q3_on_task_details},
        {'text_key': 'mw_q4_on_task_instr', 'buttons_details': q4_on_task_details},
        {'text_key': 'mw_final_note', 'buttons_details': None}
    ]

    for i, page_data in enumerate(mw_instruction_pages):
        page_num = i + 1
        total_pages = len(mw_instruction_pages)
        
        page_text = get_text_with_newlines(
            'MW_Probes', 
            page_data['text_key'], 
            default=f"Default text for: {page_data['text_key']}\n(Please add this key to your INI file)"
        )
        
        if page_num == total_pages:
            if not RUN_COMPREHENSION_QUIZ:
                prompt_key = 'prompt_continue'
                default_quiz_prompt = "(Press SPACE to continue to the main task.)"
            else:
                prompt_key = 'prompt_quiz'
                default_quiz_prompt = "(Press SPACE to continue)"
            prompt_text = get_text_with_newlines('Screens', prompt_key, default=default_quiz_prompt)
        else:
            default_continue_prompt = "(Press SPACE to continue.)"
            prompt_text = get_text_with_newlines('Screens', 'prompt_continue', default=default_continue_prompt)

        mw_message = visual.TextStim(
            win, text=page_text, color='black', height=25, wrapWidth=1000, 
            pos=(0, 250), 
            alignHoriz='center', alignVert='top', font='Arial'
        )
        
        prompt_message = visual.TextStim(
            win, text=prompt_text.strip(), color='black', height=25, wrapWidth=1000,
            pos=(0, -300), 
            alignHoriz='center', font='Arial'
        )

        win.flip() 
        mw_message.draw()
        prompt_message.draw()
        
        if page_data['buttons_details'] is not None:
            utils.draw_example_buttons(win, page_data['buttons_details'])
        
        win.flip() 
        pressed_key = None
        while pressed_key is None:
            # 1. Check Keyboard
            kb_responses = event.getKeys()
            if kb_responses:
                pressed_key = kb_responses[0]
                break

            # 2. Check Riponda (any button press)
            if riponda_port and riponda_port.in_waiting >= 6:
                try:
                    packet = riponda_port.read(6)
                    if packet[0] == 0x6b and packet[1] in mw_riponda_map:
                        pressed_key = 'riponda_press'
                        riponda_port.reset_input_buffer()
                        break
                    else:
                        riponda_port.reset_input_buffer()
                except Exception as e:
                    print(f"Riponda read error: {e}")
                    riponda_port.reset_input_buffer()
            
            core.wait(0.001)

        if pressed_key == 'escape':
            quit_experiment()
            
    # --- Quiz Implementation (Gated by Setting) ---
    if RUN_COMPREHENSION_QUIZ:
        quiz_passed = False
        quiz_attempts = 0
        MAX_QUIZ_ATTEMPTS = 3 

        while not quiz_passed and quiz_attempts < MAX_QUIZ_ATTEMPTS:
            quiz_attempts += 1 
            quiz_passed = run_comprehension_quiz(
                win, 
                quit_experiment,
                text_filename,
                attempt_number=quiz_attempts,
                riponda_port=riponda_port
            )

        if not quiz_passed:
            fail_text = get_text_with_newlines(
                'Screens', 
                'quiz_fail_continue',
                default="Unfortunately, you did not pass the comprehension quiz after 3 attempts.\nThe experiment will now continue.\n\n(Press any key to continue.)"
            )
            
            fail_message = visual.TextStim(
                win, 
                text=fail_text, 
                color='red', 
                height=30, 
                wrapWidth=1000, 
                font='Arial'
            )
            fail_message.draw()
            win.flip()
            
            pressed_key = None
            while pressed_key is None:
                # 1. Check Keyboard
                kb_responses = event.getKeys()
                if kb_responses:
                    pressed_key = kb_responses[0]
                    break 
                # 2. Check Riponda
                if riponda_port and riponda_port.in_waiting >= 6:
                    try:
                        packet = riponda_port.read(6)
                        if packet[0] == 0x6b and packet[1] in mw_riponda_map:
                            pressed_key = 'riponda_press'
                            riponda_port.reset_input_buffer()
                            break
                        else:
                            riponda_port.reset_input_buffer()
                    except Exception as e:
                        print(f"Riponda read error: {e}")
                        riponda_port.reset_input_buffer()
                core.wait(0.001)

            if pressed_key == 'escape':
                quit_experiment()