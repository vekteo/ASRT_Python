from psychopy import visual, core, event
from config_helpers import get_text_with_newlines
import experiment_utils as utils
from quiz_logic import run_comprehension_quiz

def show_mw_instructions_and_quiz(win, quit_experiment, RUN_COMPREHENSION_QUIZ, text_filename, riponda_port=None, fg_color='black', bg_color='white'):
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

    # --- Button Definition Helpers ---
    
    # Q1 Buttons (1-4 scale)
    q1_button_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_1', default="Not at all"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_4', default="Completely"), 'x': 300}
    ]

    # Q2 (Off-Task Content) Buttons
    q2_mw_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_1', default="I was thinking about nothing"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q2_mw_label_4', default="I was thinking about something in particular"), 'x': 300}
    ]

    # Q3 (Spontaneous/Deliberate) Buttons
    q3_mw_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_1', default="I was completely spontaneous"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q3_mw_label_4', default="I was completely deliberate"), 'x': 300}
    ]

    # Q4 (Affective Tone) Buttons
    q4_mw_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_1', default="Completely Negative"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_4', default="Completely Positive"), 'x': 300}
    ]

    # --- INSTRUCTION PAGES DATA ---
    mw_instruction_pages = [
        # Intro
        {'text': get_text_with_newlines('MW_Probes', 'mw_intro'), 'buttons': None},
        # Q1 Explanation
        {'text': get_text_with_newlines('MW_Probes', 'mw_q1'), 'buttons': q1_button_details},
        # Q2 Off-Task Explanation
        {'text': get_text_with_newlines('MW_Probes', 'mw_q2_off_task'), 'buttons': q2_mw_details},
        # Q3 Spontaneous Explanation
        {'text': get_text_with_newlines('MW_Probes', 'mw_q3_spontaneous'), 'buttons': q3_mw_details},
        # Q4 Affective Explanation
        {'text': get_text_with_newlines('MW_Probes', 'mw_q4_affective'), 'buttons': q4_mw_details},
        # On-Task Intro
        {'text': get_text_with_newlines('MW_Probes', 'mw_on_task_intro'), 'buttons': None},
        # On-Task Follow-up Questions Explanation
        {'text': get_text_with_newlines('MW_Probes', 'mw_on_task_follow_up'), 'buttons': None},
        # Final Note
        {'text': get_text_with_newlines('MW_Probes', 'mw_final_note'), 'buttons': None},
    ]

    # Function to draw example buttons for instructions
    def draw_instruction_buttons(details):
        if not details: return
        for detail in details:
            # Draw the button rectangle
            rect = visual.Rect(
                win=win, width=150, height=100, pos=(detail['x'], -250),
                fillColor='lightgrey', lineColor=fg_color, lineWidth=3
            )
            rect.draw()
            
            # Draw the key number inside the button
            number_stim = visual.TextStim(
                win, text=detail['key'], color='black', height=50, pos=(detail['x'], -250),
                font='Arial'
            )
            number_stim.draw()
            
            # Draw the label below the button
            label_stim = visual.TextStim(
                win, text=detail['label'], color=fg_color, height=20, pos=(detail['x'], -350), wrapWidth=200,
                font='Arial'
            )
            label_stim.draw()

    # --- DISPLAY LOOP ---
    for page in mw_instruction_pages:
        text_stim = visual.TextStim(
            win, 
            text=page['text'], 
            color=fg_color, 
            height=28, 
            pos=(0, 50), 
            wrapWidth=1700, 
            font='Arial'
        )
        
        prompt_text = get_text_with_newlines('Screens', 'prompt_continue', default="(Press any key to continue.)")
        continue_stim = visual.TextStim(
            win, 
            text=prompt_text, 
            color=fg_color, 
            height=20, 
            pos=(0, -450), 
            wrapWidth=1600, 
            font='Arial'
        )

        text_stim.draw()
        continue_stim.draw()
        
        if page['buttons']:
            draw_instruction_buttons(page['buttons'])
            
        win.flip()
        
        # Wait for input
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
                    if packet[0] == 0x6b: # Any key
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

    # --- COMPREHENSION QUIZ ---
    if RUN_COMPREHENSION_QUIZ:
        quiz_passed = False
        attempts = 0
        MAX_ATTEMPTS = 3
        
        while not quiz_passed and attempts < MAX_ATTEMPTS:
            attempts += 1
            passed = run_comprehension_quiz(win, text_filename, riponda_port=riponda_port, fg_color=fg_color, bg_color=bg_color)
            
            if passed:
                quiz_passed = True
                success_text = get_text_with_newlines('Quiz', 'quiz_passed_congrats')
                success_msg = visual.TextStim(
                    win, text=success_text, color=fg_color, height=30, wrapWidth=1600, font='Arial'
                )
                success_msg.draw()
                win.flip()
                core.wait(2.0)
                
                # Wait for key to start main task
                start_prompt = get_text_with_newlines('Quiz', 'quiz_passed_start')
                visual.TextStim(win, text=start_prompt, color=fg_color, height=30, wrapWidth=1600).draw()
                win.flip()
                
                # Simple wait
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
                            if packet[0] == 0x6b:
                                pressed_key = 'riponda_press'
                                riponda_port.reset_input_buffer()
                                break
                            else:
                                riponda_port.reset_input_buffer()
                        except Exception as e:
                            print(f"Riponda read error: {e}")
                            riponda_port.reset_input_buffer()
                    core.wait(0.001)
                
            else:
                if attempts < MAX_ATTEMPTS:
                    retry_text = get_text_with_newlines('Quiz', 'quiz_failed_retry')
                    retry_msg = visual.TextStim(
                        win, text=retry_text, color='red', height=30, wrapWidth=1600, font='Arial'
                    )
                    retry_msg.draw()
                    win.flip()
                    
                    # Wait for input
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
                                if packet[0] == 0x6b:
                                    pressed_key = 'riponda_press'
                                    riponda_port.reset_input_buffer()
                                    break
                                else:
                                    riponda_port.reset_input_buffer()
                            except Exception as e:
                                print(f"Riponda read error: {e}")
                                riponda_port.reset_input_buffer()
                        core.wait(0.001)
        
        if not quiz_passed:
            fail_text = get_text_with_newlines(
                'Screens', 
                'quiz_failure_continue', 
                default="Unfortunately, you did not pass the comprehension quiz after 3 attempts.\nThe experiment will now continue.\n\n(Press any key to continue.)"
            )
            
            fail_message = visual.TextStim(
                win, 
                text=fail_text, 
                color='red', 
                height=30, 
                wrapWidth=1600, 
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
                        if packet[0] == 0x6b:
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