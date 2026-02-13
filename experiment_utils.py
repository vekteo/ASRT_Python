from psychopy import visual, core
from datetime import datetime
import serial
import csv
import os

class LogTee:
    """Captures stdout, adds timestamps, and writes to both console and file."""
    def __init__(self, filename, original_stream):
        self.file = open(filename, 'w', encoding='utf-8')
        self.original_stream = original_stream
        self.new_line = True 

    def write(self, message):
        self.original_stream.write(message)
        self.original_stream.flush()

        if message:
            timestamp = datetime.now().strftime("[%H:%M:%S.%f]")
            
            parts = message.split('\n')
            
            for i, part in enumerate(parts):
                if self.new_line and part:
                    self.file.write(f"{timestamp} {part}")
                    self.new_line = False
                elif part:
                    self.file.write(part)
                
                if i < len(parts) - 1:
                    self.file.write('\n')
                    self.new_line = True
                    
        self.file.flush()

    def flush(self):
        self.original_stream.flush()
        self.file.flush()

    def close(self):
        self.file.close()

def send_trigger_pulse(ser_port, trigger_value, pulse_duration=0.05):
    """Sends a trigger pulse (value, duration) and resets the port to 0."""
    print(f"Trigger sent: {trigger_value}") 
    
    if ser_port:
        try:
            ser_port.write(bytes([trigger_value]))
            ser_port.flush()
            core.wait(pulse_duration) 
            ser_port.write(bytes([0]))
            ser_port.flush()
        except Exception as e:
            print(f"Error writing to serial port: {e}")
    else:
        pass

def save_and_quit(win, unique_filename, all_data):
    """Saves all collected data to the unique CSV file and quits."""
    with open(unique_filename, 'w', newline='') as csvfile:
        fieldnames = ['participant', 'session', 'block_number', 'trial_number', 'trial_in_block_num', 'trial_type', 'probability_type', 'sequence_used', 'stimulus_position_num', 'rt_non_cumulative_s', 'rt_cumulative_s', 'correct_key_pressed', 'response_key_pressed', 'correct_response', 'is_nogo', 'is_practice', 'epoch', 
                      'mind_wandering_rating_1', 'mind_wandering_rating_2', 'mind_wandering_rating_3', 'mind_wandering_rating_4']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"Experiment terminated. Data saved successfully to {unique_filename}")
    win.close()
    core.quit()

def draw_example_buttons(win, details):
    """
    Draws non-interactive buttons for instruction screens.
    Adjusts Y-position to appear below the main instruction text.
    """
    y_pos_rect = -50
    y_pos_label = -150
    
    for detail in details:
        rect = visual.Rect(
            win=win, width=150, height=100, pos=(detail['x'], y_pos_rect),
            fillColor='lightgrey', lineColor='black', lineWidth=3
        )
        rect.draw()
        number_stim = visual.TextStim(
            win, text=detail['key'], color='black', height=50, pos=(detail['x'], y_pos_rect),
            font='Arial'
        )
        number_stim.draw()
        label_stim = visual.TextStim(
            win, text=detail['label'], color='black', height=20, pos=(detail['x'], y_pos_label),
            wrapWidth=200, font='Arial'
        )
        label_stim.draw()