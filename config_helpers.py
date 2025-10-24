import configparser
import os
import io

# Global variable to store the text configuration once loaded
GLOBAL_TEXT_CONFIG = None

def set_global_text_config(config_obj):
    """Sets the global config object reference from the main script."""
    global GLOBAL_TEXT_CONFIG
    GLOBAL_TEXT_CONFIG = config_obj
    
def get_text_with_newlines(section, option, default=None):
    """
    Retrieves text from the global config object and handles escape sequences 
    for display in the main script.
    """
    global GLOBAL_TEXT_CONFIG 
    
    if GLOBAL_TEXT_CONFIG is None:
        # Fallback in case the main script didn't set the config
        print("Warning: GLOBAL_TEXT_CONFIG is not set in config_helpers. Attempting to load 'experiment_text.ini'.")
        # A minimal loading attempt for robustness, though main script should handle it
        temp_config = configparser.ConfigParser()
        try:
            temp_config.read('experiment_text_en.ini') # Defaulting to en for a simple check
            set_global_text_config(temp_config)
        except:
            pass
        
    try:
        text_content = GLOBAL_TEXT_CONFIG.get(section, option, raw=True)
        return text_content.encode().decode('unicode_escape')
    except configparser.NoOptionError:
        if default is not None:
            return default
        else:
            raise