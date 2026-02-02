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
def run_comprehension_quiz(win, save_and_quit, text_filename, attempt_number=1, riponda_port=None, fg_color='black', bg_color='white'):
    """
    Runs one round of the comprehension quiz.
    Returns True if passed (0 errors), False otherwise.
    """
    # 0x30 -> '1', 0x70 -> '2', 0xb0 -> '3', 0xf0 -> '4'
    quiz_riponda_map = {
        48: '1',  # Button 1 Press
        112: '2', # Button 2 Press
        176: '3', # Button 3 Press
        240: '4'  # Button 4 Press
    }

    def draw_quiz_screen(question_text, choices, selection=None):
        q_stim = visual.TextStim(win, text=question_text, color=fg_color, height=35, pos=(0, 200), wrapWidth=1600, font='Arial')
        q_stim.draw()
        
        choice_y = -50
        
        # Define button positions
        button_configs = [
            {'key': '1', 'pos': (-300, choice_y)},
            {'key': '4', 'pos': (300, choice_y)} 
        ]
        
        for i, choice_str in enumerate(choices):
            if i >= len(button_configs): break
            cfg = button_configs[i]
            
            fill_col = 'lightgrey'
            if selection == cfg['key']: 
                fill_col = 'skyblue' 
            
            rect = visual.Rect(win, width=400, height=150, pos=cfg['pos'], fillColor=fill_col, lineColor=fg_color, lineWidth=3)
            rect.draw()
            
            label_lookup = f"quiz_label_key_{cfg['key']}"
            key_label_text = get_text_with_newlines('Quiz', label_lookup, default=f"Key {cfg['key']}")
            
            key_stim = visual.TextStim(win, text=key_label_text, color='black', height=20, pos=(cfg['pos'][0], cfg['pos'][1] + 50), font='Arial')
            key_stim.draw()
            
            text_stim = visual.TextStim(win, text=choice_str, color='black', height=25, pos=(cfg['pos'][0], cfg['pos'][1] - 20), wrapWidth=380, font='Arial')
            text_stim.draw()

    def execute_quiz_round():
        nonlocal save_and_quit, riponda_port, quiz_riponda_map
        quiz_error_count = 0
        
        # Run Questions
        for i, q_data in enumerate(QUIZ_QUESTIONS_DATA):
            q_num = i + 1
            q_text_content = get_text_with_newlines('Quiz', q_data['q_key'])
            
            total_qs = len(QUIZ_QUESTIONS_DATA)
            header_fmt = get_text_with_newlines('Quiz', 'quiz_question_header', default="Question {q_num} of {total}:")
            header_str = header_fmt.format(q_num=q_num, total=total_qs)
            
            full_q_text = f"{header_str}\n\n{q_text_content}"
            
            choices_str = get_text_with_newlines('Quiz', q_data['c_key'])
            choices = [c.strip() for c in choices_str.split(',')]
            correct_ans_idx_str = get_text_with_newlines('Quiz', q_data['a_key'])
            
            if correct_ans_idx_str == '0':
                correct_key = '1'
            else:
                correct_key = '4'

            # Display and Wait
            answered = False
            response_key = None
            
            while not answered:
                draw_quiz_screen(full_q_text, choices)
                win.flip()
                
                # Check Inputs
                pressed = None
                
                # 1. Keyboard
                kb = event.getKeys(keyList=['1', '4', 'escape'])
                if kb:
                    if 'escape' in kb:
                        save_and_quit()
                    pressed = kb[0]
                
                # 2. Riponda
                if not pressed and riponda_port and riponda_port.in_waiting >= 6:
                    try:
                        packet = riponda_port.read(6)
                        if packet[0] == 0x6b and packet[1] in quiz_riponda_map:
                            val = quiz_riponda_map[packet[1]]
                            if val in ['1', '4']:
                                pressed = val
                            riponda_port.reset_input_buffer()
                        else:
                            riponda_port.reset_input_buffer()
                    except Exception:
                        riponda_port.reset_input_buffer()
                
                if pressed:
                    response_key = pressed
                    answered = True
            
            is_correct = (response_key == correct_key)
            
            if not is_correct:
                quiz_error_count += 1
                feedback_text = get_text_with_newlines('Quiz', 'quiz_question_feedback_incorrect')
                feedback_color = 'red'
            else:
                feedback_text = get_text_with_newlines('Quiz', 'quiz_question_feedback_correct')
                feedback_color = 'green'

            draw_quiz_screen(full_q_text, choices, selection=response_key)
            
            feedback_press_key = get_text_with_newlines('Quiz', 'quiz_press_key')
            feedback_stim = visual.TextStim(win, text=feedback_text + feedback_press_key, 
                                            color=feedback_color, height=35, pos=(0, -250), font='Arial')
            
            feedback_stim.draw()
            win.flip()
            core.wait(1.0)
            
            event.clearEvents()
            if riponda_port:
                riponda_port.reset_input_buffer()

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
            if pressed_key == 'escape':
                save_and_quit()

        return quiz_error_count

    # --- Main Quiz Flow Control ---
    
    if attempt_number == 1:
        intro_key = 'quiz_intro'
        default_intro = "You will now complete a short 9-question comprehension quiz.\n\n(Press SPACE to begin.)"
    else:
        intro_key = 'quiz_failed_retry'
        default_intro = f"You had some incorrect answers. Let's try the quiz again.\n\nThis is attempt {attempt_number}.\n\n(Press SPACE to begin.)"
    
    intro_text = get_text_with_newlines('Quiz', intro_key, default=default_intro)
    intro_stim = visual.TextStim(win, text=intro_text, color=fg_color, height=30, wrapWidth=1200, font='Arial')
    intro_stim.draw()
    win.flip()

    # FIX: Clear buffers before waiting
    event.clearEvents()
    if riponda_port:
        riponda_port.reset_input_buffer()

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

    if pressed_key == 'escape':
        save_and_quit()

    error_count = execute_quiz_round()
    
    if error_count == 0:
        final_text = get_text_with_newlines('Quiz', 'quiz_passed_congrats', default="Congratulations, you passed the quiz!\n\n(Press SPACE to continue.)")
        final_stim = visual.TextStim(win, text=final_text, color='green', wrapWidth=1600, height=40, font='Arial')
        final_stim.draw()
        win.flip()
        
        event.clearEvents()
        if riponda_port:
            riponda_port.reset_input_buffer()
        
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
        
        return True
        
    else:
        # FAILED
        correct_count = 9 - error_count
        summary_text = get_text_with_newlines(
            'Quiz', 
            'quiz_explanation_page1',
            default="You answered {correct_count} out of 9 questions correctly."
        ).format(correct_count=correct_count)
        
        press_instruction = get_text_with_newlines(
            'Quiz',
            'quiz_press_key',
            default="\n\n(Press SPACE to continue.)"
        )
        summary_text += press_instruction        
        summary_stim = visual.TextStim(win, text=summary_text, color=fg_color, height=22, wrapWidth=1200, font='Arial')
        summary_stim.draw()
        win.flip()

        event.clearEvents()
        if riponda_port:
            riponda_port.reset_input_buffer()

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