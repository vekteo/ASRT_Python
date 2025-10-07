# Import necessary PsychoPy modules used within this function
from psychopy import visual, core, event

def show_mind_wandering_probe(win, mw_testing_involved, na_mw_rating, save_and_quit_func):
    """
    Displays the Mind Wandering probe (Q1) and branches to ask three follow-up 
    questions (Q2, Q3, Q4) based on the Q1 response (1,2=MW vs. 3,4=Non-MW).
    All questions are answered by button press (1-4).
    Returns a list of four ratings (Q1, Q2, Q3, Q4) as strings.
    
    Args:
        win (psychopy.visual.Window): The experiment window.
        mw_testing_involved (bool): Flag indicating if MW testing is enabled.
        na_mw_rating (str): The value to use for Not Applicable ratings ('NA').
        save_and_quit_func (function): Reference to the main script's save_and_quit function.
    """
    # If not enabled, return list of NA ratings
    if not mw_testing_involved:
        return [na_mw_rating] * 4

    # --- Q1 SETUP: Primary Focus Question ---
    primary_question = "Q1: To what degree were you focusing on the task during the previous block?"
    
    # Q1 Response Options (shared scale and labels)
    q1_button_details = [
        {'key': '1', 'label': "Not at all", 'desc': "1 / Completely Off-Task / Thinking of something else", 'x': -400},
        {'key': '2', 'label': "", 'desc': "2 / Somewhat Off-Task", 'x': -150},
        {'key': '3', 'label': "", 'desc': "3 / Mostly On-Task", 'x': 150},
        {'key': '4', 'label': "Completely", 'desc': "4 / Completely On-Task / Highly Focused", 'x': 400}
    ]

    # --- NEW: SPECIFIC FOLLOW-UP RESPONSE OPTIONS ---
    
    # Q2: Content of thoughts (Specific labels for MW-branch)
    q2_mw_details = [
        {'key': '1', 'label': "I was thinking about nothing", 'x': -400},
        {'key': '2', 'label': "", 'x': -150},
        {'key': '3', 'label': "", 'x': 150},
        {'key': '4', 'label': "I was thinking about something in particular", 'x': 400}
    ]

    # Q3: Deliberateness of thoughts (Specific labels for MW-branch)
    q3_mw_details = [
        {'key': '1', 'label': "I was completely spontaneous", 'x': -400},
        {'key': '2', 'label': "", 'x': -150},
        {'key': '3', 'label': "", 'x': 150},
        {'key': '4', 'label': "I was completely deliberate", 'x': 400}
    ]

    # Q4: Affective tone of thoughts (Specific labels for MW-branch)
    q4_mw_details = [
        {'key': '1', 'label': "Completely positive", 'x': -400},
        {'key': '2', 'label': "", 'x': -150},
        {'key': '3', 'label': "", 'x': 150},
        {'key': '4', 'label': "Completely Negative", 'x': 400}
    ]

    # Q2: Task focus (Specific labels for Non-MW/On-Task branch)
    q2_on_task_details = [
        {'key': '1', 'label': "Focus entirely on speed", 'x': -400},
        {'key': '2', 'label': "", 'x': -150},
        {'key': '3', 'label': "", 'x': 150},
        {'key': '4', 'label': "Focus entirely on accuracy", 'x': 400}
    ]

    # Q3: Concentration difficulty (Specific labels for Non-MW/On-Task branch)
    q3_on_task_details = [
        {'key': '1', 'label': "Extremely difficult to concentrate", 'x': -400},
        {'key': '2', 'label': "", 'x': -150},
        {'key': '3', 'label': "", 'x': 150},
        {'key': '4', 'label': "Extremely easy to concentrate", 'x': 400}
    ]

    # Q4: Task Tiringness (Specific labels for Non-MW/On-Task branch)
    q4_on_task_details = [
        {'key': '1', 'label': "Not at all tiring", 'x': -400},
        {'key': '2', 'label': "", 'x': -150},
        {'key': '3', 'label': "", 'x': 150},
        {'key': '4', 'label': "Extremely tiring", 'x': 400}
    ]

    # --- FOLLOW-UP QUESTION BANK ---
    # Questions for ratings 1 or 2 (Mind Wandering related)
    mw_questions = [
        {"text": "To the degree to which you were not focusing on the task, what was the nature of your thoughts?", "details": q2_mw_details},
        {"text": "Was your mind wandering deliberate or spontaneous?", "details": q3_mw_details},
        {"text": "What was the affective (emotional) tone of your thoughts?", "details": q4_mw_details}
    ]
    # Questions for ratings 3 or 4 (Non-Mind Wandering related / On-Task)
    non_mw_questions = [
        {"text": "Did you focus more on speed or accuracy in the previous block?", "details": q2_on_task_details},
        {"text": "How difficult was it for you to concentrate on the task in the previous block?", "details": q3_on_task_details},
        {"text": "How tiring did you find the task?", "details": q4_on_task_details}
    ]

    ratings = []

    def draw_buttons(details):
        buttons_list = []
        for detail in details:
            # Visual Button (Rectangle)
            rect = visual.Rect(
                win=win, width=150, height=100, pos=(detail['x'], 0),
                fillColor='lightgrey', lineColor='black', lineWidth=3,
                autoDraw=True
            )
            # Number Label
            number_stim = visual.TextStim(
                win, text=detail['key'], color='black', height=50, pos=(detail['x'], 0),
                autoDraw=True
            )
            # Text Description
            label_stim = visual.TextStim(
                win, text=detail['label'], color='black', height=20, pos=(detail['x'], -100), wrapWidth=200,
                autoDraw=True
            )
            buttons_list.append({'rect': rect, 'number': number_stim, 'label': label_stim, 'rating': detail['key']})
        return buttons_list

    def display_and_collect_rating(question_text, buttons_details):
        # 1. Setup Stimuli for current question
        question_stim = visual.TextStim(win, text=question_text, color='black', height=40, pos=(0, 200), wrapWidth=1000)
        
        buttons = draw_buttons(buttons_details)

        # 2. Draw and Collect KEYBOARD Response
        win.mouseVisible = False 
        question_stim.draw()
        win.flip()

        valid_keys = ['1', '2', '3', '4', 'escape']
        response = event.waitKeys(keyList=valid_keys)
        pressed_key = response[0]

        if pressed_key == 'escape':
            # Use the passed function reference for clean termination
            save_and_quit_func()
            return 'quit'

        rating = pressed_key

        # 3. Provide visual feedback
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

        # 4. Clean up
        for b in buttons:
            b['rect'].autoDraw = False
            b['number'].autoDraw = False
            b['label'].autoDraw = False
        
        return rating

    # --- Q1: Collect Primary Focus Rating ---
    rating_1 = display_and_collect_rating(primary_question, q1_button_details)
    if rating_1 == 'quit':
        return [na_mw_rating] * 4
    ratings.append(rating_1)

    # --- Determine Follow-up Questions and Details ---
    if rating_1 in ['1', '2']:
        follow_up_data = mw_questions
    else: # rating_1 is '3' or '4'
        follow_up_data = non_mw_questions
    
    # --- Q2, Q3, Q4: Collect Follow-up Ratings ---
    for i, q_data in enumerate(follow_up_data):
        question_num = i + 2
        
        # **Crucially, use the specific question text and button details from the list**
        full_question = f"Q{question_num}: {q_data['text']} (Press 1-4)"
        
        rating_n = display_and_collect_rating(full_question, q_data['details'])
        
        if rating_n == 'quit':
             # If quitting midway, pad the rest with NA and return the partial list
            return ratings + [na_mw_rating] * (4 - len(ratings)) 
        ratings.append(rating_n)

    # Return all four ratings [Q1, Q2, Q3, Q4]
    return ratings