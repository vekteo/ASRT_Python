# Import necessary modules from PsychoPy and Python core
from psychopy import visual, core, event
import configparser
import io
import os
from config_helpers import get_text_with_newlines

# --- QUIZ DATA STRUCTURE ---
QUIZ_QUESTIONS_DATA = [
    {'q_key': 'quiz_q1_text', 'a_key': 'quiz_q1_answer', 'c_key': 'quiz_choices_focus'},
    {'q_key': 'quiz_q2_text', 'a_key': 'quiz_q2_answer', 'c_key': 'quiz_choices_focus'},
    {'q_key': 'quiz_q3_text', 'a_key': 'quiz_q3_answer', 'c_key': 'quiz_choices_focus'},
    {'q_key': 'quiz_q4_text', 'a_key': 'quiz_q4_answer', 'c_key': 'quiz_choices_focus'},
    {'q_key': 'quiz_q5_text', 'a_key': 'quiz_q5_answer', 'c_key': 'quiz_choices_focus'},
    {'q_key': 'quiz_q6_text', 'a_key': 'quiz_q6_answer', 'c_key': 'quiz_choices_focus'},
    {'q_key': 'quiz_q7_text', 'a_key': 'quiz_q7_answer', 'c_key': 'quiz_choices_content'},
    {'q_key': 'quiz_q8_text', 'a_key': 'quiz_q8_answer', 'c_key': 'quiz_choices_spontaneous'},
    {'q_key': 'quiz_q9_text', 'a_key': 'quiz_q9_answer', 'c_key': 'quiz_choices_tone'},
]

# --- MAIN FUNCTION FOR QUIZ EXECUTION ---
# --- CHANGED: Added riponda_port=None to the signature ---
def run_comprehension_quiz(win, save_and_quit, text_filename, attempt_number=1, riponda_port=None):
    """
    Runs one round of the comprehension quiz.
    Returns True if passed (0 errors), False otherwise.
    """
    
    # --- ADDED: Local Riponda map for MW/Quiz screens (1, 2, 3, 4) ---
    # Maps the "press" byte (from your test) directly to the number string
    # 0x30 -> '1', 0x70 -> '2', 0xb0 -> '3', 0xf0 -> '4'
    quiz_riponda_map = {
        48: '1',  # Button 1 Press
        112: '2', # Button 2 Press
        176: '3', # Button 3 Press
        240: '4'  # Button 4 Press
    }
    # --- END ADD ---

    # --- CHANGED: Added riponda_port and byte_map to the signature ---
    def display_quiz_question(q_num, q_text, choices_str, riponda_port=None, byte_map=None):
        choices = [c.strip() for c in choices_str.split(',')]
        
        question_display = f"Question {q_num} of 9:\n\n{q_text}\n\n"
        
        if len(choices) == 2:
            # Special logic for 2 choices: keys 1 and 4
            question_display += f"Press 1: {choices[0]}\n"
            question_display += f"Press 4: {choices[1]}\n"
            valid_keys = ['1', '4', 'escape']
        else:
            # Original logic for 1, 3, or 4 choices
            for i, choice in enumerate(choices):
                question_display += f"Press {i+1}: {choice}\n" 
            valid_keys = [str(i+1) for i in range(len(choices))] + ['escape']
            
        q_stim = visual.TextStim(win, text=question_display, color='black', height=30, 
                                 wrapWidth=1200, font='Arial', alignHoriz='center', alignVert='center')
        
        q_stim.draw()
        win.flip()
        
        # --- CHANGED: Replaced event.waitKeys() with a custom polling loop ---
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
                        # Find out which key was pressed (e.g., '1', '2', '3', '4')
                        riponda_key = byte_map[packet[1]] 
                        
                        # IMPORTANT: Check if this key is a VALID answer for this question
                        if riponda_key in valid_keys: 
                            pressed_key = riponda_key
                            riponda_port.reset_input_buffer()
                            break
                        else:
                            # Pressed a key (e.g., '2'), but it's not a valid option ('1' or '4')
                            riponda_port.reset_input_buffer() # Ignore and wait
                    else:
                        riponda_port.reset_input_buffer() # Ignore release packets
                except Exception as e:
                    print(f"Riponda read error: {e}")
                    riponda_port.reset_input_buffer()
            
            core.wait(0.001) # Don't fry the CPU
        # --- END CHANGE ---
            
        if pressed_key == 'escape':
            save_and_quit()
            
        return pressed_key # Was response[0]

    # Function to execute one full quiz round and return error count
    def execute_quiz_round():
        nonlocal save_and_quit, riponda_port, quiz_riponda_map # --- ADDED ---
        quiz_error_count = 0
        
        # Run Questions
        for i, q_data in enumerate(QUIZ_QUESTIONS_DATA):
            q_num = i + 1
            
            # --- CHANGED: Using the correct, imported function ---
            q_text = get_text_with_newlines('Quiz', q_data['q_key'])
            choices_str = get_text_with_newlines('Quiz', q_data['c_key'])
            correct_ans_str = get_text_with_newlines('Quiz', q_data['a_key'])
            
            # --- CHANGED: Pass Riponda info to the helper function ---
            response_key = display_quiz_question(
                q_num, q_text, choices_str,
                riponda_port=riponda_port,
                byte_map=quiz_riponda_map
            )
            
            # --- Map response key ('1' or '4') to 0-based index ('0' or '1') ---
            num_choices = len(choices_str.split(','))
            
            if num_choices == 2 and response_key == '4':
                # Map '4' to index '1' ONLY for 2-choice questions
                response_index_str = '1'
            else:
                # Original logic works for '1', '2', '3'
                # and for '1' in the 2-choice case
                response_index_str = str(int(response_key) - 1)
                
            is_correct = (response_index_str == correct_ans_str)
            
            if not is_correct:
                quiz_error_count += 1
                feedback_text = "Incorrect."
                feedback_color = 'red'
            else:
                feedback_text = "Correct! "
                feedback_color = 'green'

            feedback_stim = visual.TextStim(win, text=feedback_text + "\n\nPress SPACE to continue.", 
                                            color=feedback_color, height=35, font='Arial')
            
            feedback_stim.draw()
            win.flip()

            # --- CHANGED: Replaced event.waitKeys() with polling loop ---
            # This loop accepts 'space' or *any* Riponda button press
            pressed_key = None
            while pressed_key is None:
                # 1. Check Keyboard
                kb_responses = event.getKeys(keyList=['space', 'escape'])
                if kb_responses:
                    pressed_key = kb_responses[0]
                    break
                # 2. Check Riponda (any button press)
                if riponda_port and riponda_port.in_waiting >= 6:
                    try:
                        packet = riponda_port.read(6)
                        if packet[0] == 0x6b and packet[1] in quiz_riponda_map:
                            pressed_key = 'riponda_press' # Acts like 'space'
                            riponda_port.reset_input_buffer()
                            break
                        else:
                            riponda_port.reset_input_buffer()
                    except Exception as e:
                        print(f"Riponda read error: {e}")
                        riponda_port.reset_input_buffer()
                core.wait(0.001)
            # --- END CHANGE ---

            if pressed_key == 'escape':
                save_and_quit()

        return quiz_error_count

    # --- Main Quiz Flow Control ---
    
    # 1. Display Quiz Introduction based on attempt number
    if attempt_number == 1:
        intro_key = 'quiz_intro'
        default_intro = "You will now complete a short 9-question comprehension quiz.\n\n(Press SPACE to begin.)"
    else:
        intro_key = 'quiz_failed_retry'
        default_intro = f"You had some incorrect answers. Let's try the quiz again.\n\nThis is attempt {attempt_number}.\n\n(Press SPACE to begin.)"
    
    intro_text = get_text_with_newlines('Quiz', intro_key, default=default_intro)
    intro_stim = visual.TextStim(win, text=intro_text, color='black', height=30, wrapWidth=1200, font='Arial')
    intro_stim.draw()
    win.flip()

    # --- CHANGED: Replaced event.waitKeys() with polling loop ---
    pressed_key = None
    while pressed_key is None:
        kb_responses = event.getKeys(keyList=['space', 'escape'])
        if kb_responses:
            pressed_key = kb_responses[0]
            break
        if riponda_port and riponda_port.in_waiting >= 6:
            try:
                packet = riponda_port.read(6)
                if packet[0] == 0x6b and packet[1] in quiz_riponda_map:
                    pressed_key = 'riponda_press'
                    riponda_port.reset_input_buffer()
                    break
                else:
                    riponda_port.reset_input_buffer()
            except Exception as e:
                print(f"Riponda read error: {e}")
                riponda_port.reset_input_buffer()
        core.wait(0.001)
    # --- END CHANGE ---

    if pressed_key == 'escape':
        save_and_quit()

    # 2. Execute one round
    error_count = execute_quiz_round()
    
    # 3. Check results and return True (Pass) or False (Fail)
    if error_count == 0:
        # PASSED
        final_text = get_text_with_newlines('Quiz', 'quiz_passed_congrats', default="Congratulations, you passed the quiz!\n\n(Press SPACE to continue.)")
        final_stim = visual.TextStim(win, text=final_text, color='green', height=40, font='Arial')
        final_stim.draw()
        win.flip()
        
        # --- CHANGED: Replaced event.waitKeys() with polling loop ---
        pressed_key = None
        while pressed_key is None:
            kb_responses = event.getKeys(keyList=['space', 'escape'])
            if kb_responses:
                pressed_key = kb_responses[0]
                break
            if riponda_port and riponda_port.in_waiting >= 6:
                try:
                    packet = riponda_port.read(6)
                    if packet[0] == 0x6b and packet[1] in quiz_riponda_map:
                        pressed_key = 'riponda_press'
                        riponda_port.reset_input_buffer()
                        break
                    else:
                        riponda_port.reset_input_buffer()
                except Exception as e:
                    print(f"Riponda read error: {e}")
                    riponda_port.reset_input_buffer()
            core.wait(0.001)
        # --- END CHANGE ---
        
        return True
        
    else:
        # FAILED
        correct_count = 9 - error_count
        
        # Display failure/summary message
        summary_text = get_text_with_newlines(
            'Quiz', 
            'quiz_explanation_page1', # This text key is used for the "you failed" summary
            default="You answered {correct_count} out of 9 questions correctly."
        ).format(correct_count=correct_count)
        
        
        summary_text += "\n\n(Press SPACE to continue.)"

        summary_stim = visual.TextStim(win, text=summary_text, color='black', height=22, wrapWidth=1200, font='Arial')
        summary_stim.draw()
        win.flip()

        # --- CHANGED: Replaced event.waitKeys() with polling loop ---
        pressed_key = None
        while pressed_key is None:
            kb_responses = event.getKeys(keyList=['space', 'escape'])
            if kb_responses:
                pressed_key = kb_responses[0]
                break
            if riponda_port and riponda_port.in_waiting >= 6:
                try:
                    packet = riponda_port.read(6)
                    if packet[0] == 0x6b and packet[1] in quiz_riponda_map:
                        pressed_key = 'riponda_press'
                        riponda_port.reset_input_buffer()
                        break
                    else:
                        riponda_port.reset_input_buffer()
                except Exception as e:
                    print(f"Riponda read error: {e}")
                    riponda_port.reset_input_buffer()
            core.wait(0.001)
        # --- END CHANGE ---

        return False