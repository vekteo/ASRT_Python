from psychopy import visual, core, event
from config_helpers import get_text_with_newlines
import experiment_utils as utils

# --- MAIN PROBE FUNCTION ---
def show_mind_wandering_probe(win, ser_port, mw_testing_involved, na_mw_rating, save_and_quit_func, riponda_port=None, fg_color='black', bg_color='white'):
    """
    Displays the Mind Wandering probe (Q1) and branches to ask three follow-up 
    questions (Q2, Q3, Q4) based on the Q1 response (1,2=MW vs. 3,4=Non-MW).
    All questions are answered by button press (1-4).
    Returns a list of four ratings (Q1, Q2, Q3, Q4) as strings.
    """
    if not mw_testing_involved:
        return [na_mw_rating] * 4

    mw_riponda_map = {
        48: '1',  # Button 1 Press
        112: '2', # Button 2 Press
        176: '3', # Button 3 Press
        240: '4'  # Button 4 Press
    }

    # --- Q1 SETUP: Primary Focus Question ---
    primary_question = get_text_with_newlines('MW_Probe_Content', 'q1_primary_question', default="Q1: To what degree were you focusing on the task?")
    
    # Q1 Response Options
    q1_button_details = [
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_1', default="Not at all"), 'desc': "1 / Completely Off-Task / Thinking of something else", 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_2', default=""), 'desc': "2 / Somewhat Off-Task", 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_3', default=""), 'desc': "3 / Mostly On-Task", 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q1_label_4', default="Completely"), 'desc': "4 / Completely On-Task / Highly Focused", 'x': 300}
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
        {'key': '1', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_1', default="Completely Negative"), 'x': -300},
        {'key': '2', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_2', default=""), 'x': -100},
        {'key': '3', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_3', default=""), 'x': 100},
        {'key': '4', 'label': get_text_with_newlines('MW_Probe_Content', 'q4_mw_label_4', default="Completely Positive"), 'x': 300}
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

    # --- FOLLOW-UP QUESTION BANK ---
    mw_questions = [
        {"text": get_text_with_newlines('MW_Probe_Content', 'q2_mw_question', default="To the degree to which you were not focusing on the task, what was the nature of your thoughts?"), "details": q2_mw_details},
        {"text": get_text_with_newlines('MW_Probe_Content', 'q3_mw_question', default="Was your mind wandering deliberate or spontaneous?"), "details": q3_mw_details},
        {"text": get_text_with_newlines('MW_Probe_Content', 'q4_mw_question', default="What was the affective (emotional) tone of your thoughts?"), "details": q4_mw_details}
    ]
    non_mw_questions = [
        {"text": get_text_with_newlines('MW_Probe_Content', 'q2_on_task_question', default="Did you focus more on speed or accuracy in the previous block?"), "details": q2_on_task_details},
        {"text": get_text_with_newlines('MW_Probe_Content', 'q3_on_task_question', default="How difficult was it for you to concentrate on the task in the previous block?"), "details": q3_on_task_details},
        {"text": get_text_with_newlines('MW_Probe_Content', 'q4_on_task_question', default="How tiring did you find the task?"), "details": q4_on_task_details}
    ]

    ratings = []

    def draw_buttons(details):
        buttons_list = []
        for detail in details:
            rect = visual.Rect(
                win=win, width=150, height=100, pos=(detail['x'], 0),
                fillColor='lightgrey', lineColor=fg_color, lineWidth=3,
                autoDraw=True
            )
            number_stim = visual.TextStim(
                win, text=detail['key'], color='black', height=50, pos=(detail['x'], 0),
                autoDraw=True, font='Arial'
            )
            label_stim = visual.TextStim(
                win, text=detail['label'], color=fg_color, height=20, pos=(detail['x'], -100), wrapWidth=200,
                autoDraw=True, font='Arial'
            )
            buttons_list.append({'rect': rect, 'number': number_stim, 'label': label_stim, 'rating': detail['key']})
        return buttons_list

    def display_and_collect_rating(question_text, buttons_details, question_onset_trigger, response_base_trigger, riponda_port=None, byte_map=None, initial_wait=0.0):
        
        # --- INPUT PROTECTION DELAY (BEFORE APPEARANCE) ---
        if initial_wait > 0:
            win.flip()
            core.wait(initial_wait)
            event.clearEvents()
            if riponda_port:
                riponda_port.reset_input_buffer()
        # ------------------------------

        question_stim = visual.TextStim(win, text=question_text, color=fg_color, height=40, pos=(0, 200), wrapWidth=1600, font='Arial')
        
        buttons = draw_buttons(buttons_details)

        win.mouseVisible = False 
        question_stim.draw()
        win.flip()

        # Send Question Onset Trigger
        utils.send_trigger_pulse(ser_port, question_onset_trigger)
        print(f"MW Question Onset Trigger: {question_onset_trigger}")
        
        valid_keys = ['1', '2', '3', '4', 'escape']
        
        pressed_key = None
        while pressed_key is None:
            # 1. Check Keyboard
            kb_responses = event.getKeys(keyList=valid_keys)
            if kb_responses:
                pressed_key = kb_responses[0]
                break 

            # 2. Check Riponda
            if riponda_port and byte_map and riponda_port.in_waiting >= 6:
                try:
                    packet = riponda_port.read(6)
                    if packet[0] == 0x6b and packet[1] in byte_map:
                        pressed_key = byte_map[packet[1]] 
                        riponda_port.reset_input_buffer()
                        break 
                    else:
                        riponda_port.reset_input_buffer()
                except Exception as e:
                    print(f"Riponda read error: {e}")
                    riponda_port.reset_input_buffer()
            core.wait(0.001)

        if pressed_key == 'escape':
            save_and_quit_func()
            return 'quit'

        rating = pressed_key

        try:
            response_val = int(rating) 
            response_trigger = response_base_trigger + response_val
            utils.send_trigger_pulse(ser_port, response_trigger)
            print(f"MW Response Trigger: {response_trigger} (Base: {response_base_trigger}, Ans: {response_val})")
        except ValueError:
            print(f"Error: Could not parse rating '{rating}' for trigger.")

        # Provide visual feedback
        try:
            selected_button_index = int(rating) - 1 
            selected_button = buttons[selected_button_index]
            selected_button['rect'].fillColor = 'green'
            
            question_stim.draw()
            for b in buttons:
                b['rect'].draw()
                b['number'].draw()
                b['label'].draw()
            win.flip()
            
            core.wait(0.5) 
        except IndexError:
            pass

        # Clean up
        for b in buttons:
            b['rect'].autoDraw = False
            b['number'].autoDraw = False
            b['label'].autoDraw = False
        
        return rating

    # --- Q1: Collect Primary Focus Rating ---
    rating_1 = display_and_collect_rating(
        primary_question, 
        q1_button_details,
        question_onset_trigger=171,
        response_base_trigger=35, 
        riponda_port=riponda_port,
        byte_map=mw_riponda_map,
        initial_wait=1.0 
    )
    if rating_1 == 'quit':
        return [na_mw_rating] * 4
    ratings.append(rating_1)

    # --- Determine Follow-up Questions and Details ---
    if rating_1 in ['1', '2']:
        follow_up_data = mw_questions
        # MW Branch Trigger Logic
        onset_triggers = [172, 173, 174]
        response_bases = [40, 45, 50] 
    else:
        follow_up_data = non_mw_questions
        # On-Task Branch Trigger Logic
        onset_triggers = [175, 176, 177]
        response_bases = [55, 60, 65] 
    
    # --- Q2, Q3, Q4: Collect Follow-up Ratings ---
    for i, q_data in enumerate(follow_up_data):
        question_num = i + 2
        full_question = f"Q{question_num}: {q_data['text']}"
        
        q_onset_trigger = onset_triggers[i]
        q_response_base = response_bases[i]
        
        rating_n = display_and_collect_rating(
            full_question, 
            q_data['details'],
            q_onset_trigger,
            q_response_base,
            riponda_port=riponda_port, 
            byte_map=mw_riponda_map      
        )
        
        if rating_n == 'quit':
             return ratings + [na_mw_rating] * (4 - len(ratings)) 
        ratings.append(rating_n)

    return ratings