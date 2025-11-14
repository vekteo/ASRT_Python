import configparser

# Global variable to hold the single, central text configuration
GLOBAL_TEXT_CONFIG = None

def set_global_text_config(config_object):
    """
    Sets the global text config object for all modules to use.
    This is called from main_experiment.py.
    """
    global GLOBAL_TEXT_CONFIG
    GLOBAL_TEXT_CONFIG = config_object

def get_text_with_newlines(section, option, default=None):
    """
    Retrieves text from the GLOBAL config, converts escaped newlines (\n),
    and provides a default if the option is not found.
    
    This version correctly handles special UTF-8 characters.
    """
    global GLOBAL_TEXT_CONFIG
    
    if GLOBAL_TEXT_CONFIG is None:
        print("Error in config_helpers: GLOBAL_TEXT_CONFIG has not been set.")
        return default if default is not None else "CONFIG_ERROR"
    
    try:
        text_content = GLOBAL_TEXT_CONFIG.get(section, option, raw=True)
        return text_content.encode('latin-1').decode('unicode_escape')
        
    except (configparser.NoOptionError, configparser.NoSectionError):
        if default is not None:
            return default
        else:
            print(f"Error: Missing config text for [{section}] -> {option}")
            return f"MISSING_TEXT: [{section}] {option}"