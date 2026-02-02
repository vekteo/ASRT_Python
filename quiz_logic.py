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

def run_comprehension_quiz(win, text_filename, riponda_port=None, fg_color='black', bg_color='white'):
    """
    Runs the comprehension quiz.
    Returns True if passed (all correct), False otherwise.
    """
    
    quiz_riponda_map = {
        48: '1',  # Button 1
        112: '2', # Button 2
        176: '3', # Button 3
        240: '4'  # Button 4
    }

    # Intro Screen
    intro_text = get_text_with_newlines('Quiz', 'quiz_intro')
    intro_stim = visual.TextStim(win, text=intro_text, color=fg_color, height=30, wrapWidth=1600, font='Arial')
    intro_stim.draw()
    win.flip()
    
    # Wait for input
    pressed_key = None
    while pressed_key is None:
        kb_responses = event.getKeys()
        if kb_responses:
            pressed_key = kb_responses[0]
            break
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

    error_count = 0
    
    # --- HELPER: Draw Quiz Screen ---
    def draw_quiz_screen(question_text, choices, selection=None):
        q_stim = visual.TextStim(win, text=question_text, color=fg_color, height=35, pos=(0, 200), wrapWidth=1600, font='Arial')
        q_stim.draw()
        
        choice_y = -50
        
        # If 2 choices
        button_configs = [
            {'key': '1', 'pos': (-300, choice_y)},
            {'key': '2', 'pos': (300, choice_y)} 
        ]
        
        for i, choice_str in enumerate(choices):
            if i >= len(button_configs): break
            cfg = button_configs[i]
            
            # Highlight if selected
            fill_col = 'lightgrey'
            if selection == str(i):
                fill_col = 'skyblue'
            
            rect = visual.Rect(win, width=400, height=150, pos=cfg['pos'], fillColor=fill_col, lineColor=fg_color, lineWidth=3)
            rect.draw()
            
            # Key label (Translated)
            label_lookup = f"quiz_label_key_{cfg['key']}"
            key_label_text = get_text_with_newlines('Quiz', label_lookup, default=f"Key {cfg['key']}")
            
            key_stim = visual.TextStim(win, text=key_label_text, color='black', height=20, pos=(cfg['pos'][0], cfg['pos'][1] + 50), font='Arial')
            key_stim.draw()
            
            # Choice text
            text_stim = visual.TextStim(win, text=choice_str, color='black', height=25, pos=(cfg['pos'][0], cfg['pos'][1] - 20), wrapWidth=380, font='Arial')
            text_stim.draw()

    # --- MAIN LOOP THROUGH QUESTIONS ---
    for q_data in QUIZ_QUESTIONS_DATA:
        q_text = get_text_with_newlines('Quiz', q_data['q_key'])
        choices_str = get_text_with_newlines('Quiz', q_data['c_key'])
        choices = choices_str.split(',')
        correct_answer_idx = int(get_text_with_newlines('Quiz', q_data['a_key']))
        
        answered = False
        user_response_idx = -1
        
        # Wait for valid response
        while not answered:
            draw_quiz_screen(q_text, choices)
            win.flip()
            
            pressed = None
            
            # 1. Keyboard
            kb = event.getKeys(keyList=['1', '2', 'escape'])
            if kb:
                if 'escape' in kb:
                    core.quit()
                pressed = kb[0]
            
            # 2. Riponda
            if not pressed and riponda_port and riponda_port.in_waiting >= 6:
                try:
                    packet = riponda_port.read(6)
                    if packet[0] == 0x6b and packet[1] in quiz_riponda_map:
                        val = quiz_riponda_map[packet[1]]
                        if val in ['1', '2']:
                            pressed = val
                        riponda_port.reset_input_buffer()
                    else:
                        riponda_port.reset_input_buffer()
                except Exception:
                    riponda_port.reset_input_buffer()
            
            if pressed:
                if pressed == '1': user_response_idx = 0
                elif pressed == '2': user_response_idx = 1
                answered = True
        
        # Feedback
        is_correct = (user_response_idx == correct_answer_idx)
        if not is_correct:
            error_count += 1
            fb_text = get_text_with_newlines('Quiz', 'quiz_question_feedback_incorrect', default="Incorrect!")
            fb_color = 'red'
        else:
            fb_text = get_text_with_newlines('Quiz', 'quiz_question_feedback_correct', default="Correct!")
            fb_color = 'green'
            
        # Show Feedback Screen
        draw_quiz_screen(q_text, choices, selection=str(user_response_idx))
        
        fb_stim = visual.TextStim(win, text=fb_text, color=fb_color, height=40, pos=(0, -250), font='Arial')
        fb_stim.draw()
        
        press_msg = get_text_with_newlines('Quiz', 'quiz_press_key', default="\n\nPress any key to continue.")
        cont_stim = visual.TextStim(win, text=press_msg, color=fg_color, height=20, pos=(0, -350), font='Arial')
        cont_stim.draw()
        
        win.flip()
        core.wait(0.5) # Short wait so they see it
        
        # Wait for key to continue
        pressed_key = None
        while pressed_key is None:
            kb_responses = event.getKeys()
            if kb_responses:
                pressed_key = kb_responses[0]
                break
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
            
    # --- END OF QUIZ ---
    if error_count == 0:
        # PASSED
        return True
        
    else:
        # FAILED
        correct_count = 9 - error_count
        summary_text = get_text_with_newlines(
            'Quiz', 
            'quiz_explanation_page1',
            default="You answered {correct_count} out of 9 questions correctly."
        ).format(correct_count=correct_count)
        
        summary_text += "\n\n(Press SPACE to continue.)"

        summary_stim = visual.TextStim(win, text=summary_text, color=fg_color, height=22, wrapWidth=1600, font='Arial')
        summary_stim.draw()
        win.flip()

        pressed_key = None
        while pressed_key is None:
            kb_responses = event.getKeys()
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
        
        return False