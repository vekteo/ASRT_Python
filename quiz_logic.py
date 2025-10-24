# Import necessary modules from PsychoPy and Python core
from psychopy import visual, core, event
import configparser
import io
import os

# NOTE: This assumes get_text_with_newlines is also accessible/imported, 
# but for a simple helper, we will copy the logic needed to access the config.

MW_TEXT_CONFIG = None

def get_text_with_newlines_quiz(section, option, default=None):
    """Retrieves text and handles escape sequences for display, locally to quiz_logic."""
    global MW_TEXT_CONFIG
    try:
        text_content = MW_TEXT_CONFIG.get(section, option, raw=True)
        return text_content.encode().decode('unicode_escape')
    except configparser.NoOptionError:
        if default is not None:
            return default
        else:
            raise

def load_quiz_config(filename=None):
    """Loads the experiment_text.ini file for use within this module."""
    global MW_TEXT_CONFIG
    
    load_filename = filename if filename else 'experiment_text.ini'
    
    if MW_TEXT_CONFIG is None or filename:
        MW_TEXT_CONFIG = configparser.ConfigParser()
        try:
            if os.path.exists(load_filename):
                with io.open(load_filename, mode='r', encoding='utf-8-sig') as f:
                    file_content = f.read()
                file_content = file_content.strip()
                MW_TEXT_CONFIG.read_string(file_content)
        except Exception as e:
            print(f"Error loading quiz config ({load_filename}): {e}")

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
def run_comprehension_quiz(win, save_and_quit, text_filename):
    """
    Runs the comprehension quiz, loading text via the provided filename, 
    and enforcing pass/fail logic with retry loops.
    """
    # Load the specific language file using the provided filename
    load_quiz_config(filename=text_filename)

    # Helper to display a single question and get keyboard input ('1', '2')
    def display_quiz_question(q_num, q_text, choices_str):
        choices = [c.strip() for c in choices_str.split(',')]
        
        question_display = f"Question {q_num} of 9:\n\n{q_text}\n\n"
        for i, choice in enumerate(choices):
            question_display += f"Press {i+1}: {choice}\n" 
        
        # NOTE: Using font='Arial' for accent reliability
        q_stim = visual.TextStim(win, text=question_display, color='black', height=30, 
                                 wrapWidth=1000, font='Arial', alignHoriz='center', alignVert='center')
        
        q_stim.draw()
        win.flip()
        
        response = event.waitKeys(keyList=['1', '2', '3', 'escape'])
        
        if 'escape' in response:
            save_and_quit()
            
        return response[0]

    # Function to execute one full quiz round
    def execute_quiz_round():
        nonlocal save_and_quit
        quiz_error_count = 0
        
        # Display Quiz Introduction
        intro_text = get_text_with_newlines_quiz('Quiz', 'quiz_intro')
        intro_stim = visual.TextStim(win, text=intro_text, color='black', height=30, wrapWidth=1000, font='Arial')
        intro_stim.draw()
        win.flip()
        event.waitKeys(keyList=['space', 'escape'])

        # Run Questions
        for i, q_data in enumerate(QUIZ_QUESTIONS_DATA):
            q_num = i + 1
            
            q_text = get_text_with_newlines_quiz('Quiz', q_data['q_key'])
            choices_str = get_text_with_newlines_quiz('Quiz', q_data['c_key'])
            correct_ans_str = get_text_with_newlines_quiz('Quiz', q_data['a_key'])
            
            response_key = display_quiz_question(q_num, q_text, choices_str)
            
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
            event.waitKeys(keyList=['space', 'escape'])

        return quiz_error_count

    # --- Main Quiz Flow Control ---
    
    error_count = execute_quiz_round()
    
    while error_count > 0:
        
        correct_count = 9 - error_count
        
        # Display Summary/Explanation Pages (Uses simplified text structure for cross-language compatibility)
        summary_text = get_text_with_newlines_quiz('Quiz', 'quiz_explanation_page1').format(correct_count=correct_count)
        
        # Display summary and decision screen
        decision_text = f"Quiz finished. You answered {correct_count} out of 9 questions correctly.\n\n"
        decision_text += get_text_with_newlines_quiz('Quiz', 'quiz_passed_start') + " (PRESS 1)\n"
        decision_text += get_text_with_newlines_quiz('Quiz', 'quiz_failed_retry') + " (PRESS 2)"
        
        decision_stim = visual.TextStim(win, text=decision_text, color='black', height=35, wrapWidth=1000, font='Arial')
        decision_stim.draw()
        win.flip()
        
        decision = event.waitKeys(keyList=['1', '2', 'escape'])
        
        if 'escape' in decision or decision[0] == '1':
            break 
        else:
            error_count = execute_quiz_round()
    
    # Display Final Status
    if error_count == 0:
        final_text = get_text_with_newlines_quiz('Quiz', 'quiz_passed_congrats')
        final_stim = visual.TextStim(win, text=final_text, color='green', height=40, font='Arial')
        final_stim.draw()
        win.flip()
        event.waitKeys(keyList=['space', 'escape'])
    
    return True