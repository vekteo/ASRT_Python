import random
# Note: configparser and numpy are not needed here, only random is required for sampling

def select_nogo_trials_in_block(block_indices, pre_block_trials, num_nogo_p, num_nogo_r):
    """
    Selects indices for no-go trials from a list of pre-block trials,
    ensuring no two no-go trials are consecutive.

    Args:
        block_indices (range): Range of indices for the current block.
        pre_block_trials (list): List of dictionaries containing trial type and number.
        num_nogo_p (int): Number of no-go trials required for 'P' (Pattern) trials.
        num_nogo_r (int): Number of no-go trials required for 'R' (Random) trials.
        
    Returns:
        list: A sorted list of indices within the block that should be no-go trials.
    """
    # Filter for eligible 'P' and 'R' trials (skipping the first two trials in the block)
    p_indices = [i for i, trial in enumerate(pre_block_trials) if trial['trial_type'] == 'P' and trial['trial_in_block_num'] > 2]
    r_indices = [i for i, trial in enumerate(pre_block_trials) if trial['trial_type'] == 'R' and trial['trial_in_block_num'] > 2]

    # Validation checks
    if num_nogo_p > len(p_indices):
        raise ValueError(f"Not enough 'P' trials available for no-go selection. Requested: {num_nogo_p}, Available: {len(p_indices)}")
    if num_nogo_r > len(r_indices):
        raise ValueError(f"Not enough 'R' trials available for no-go selection. Requested: {num_nogo_r}, Available: {len(r_indices)}")

    # Attempt to sample non-consecutive no-go trials
    attempts = 0
    while attempts < 1000:
        try:
            selected_p = random.sample(p_indices, num_nogo_p)
            selected_r = random.sample(r_indices, num_nogo_r)
            temp_nogo_indices = sorted(selected_p + selected_r)
            
            # Check for consecutives
            is_consecutive = any(temp_nogo_indices[i+1] == temp_nogo_indices[i] + 1 for i in range(len(temp_nogo_indices) - 1))
            if not is_consecutive:
                return temp_nogo_indices
        except ValueError:
            # Should only happen if sampling fails unexpectedly, but good to catch
            pass
        attempts += 1
    
    # Fallback to general pool if specific type selection fails repeatedly
    eligible_indices = p_indices + r_indices
    if num_nogo_p + num_nogo_r > len(eligible_indices):
        # This should have been caught by initial checks, but acts as a safeguard
        raise ValueError(f"Not enough eligible trials for no-go selection. Requested: {num_nogo_p + num_nogo_r}, Available: {len(eligible_indices)}")

    attempts = 0
    while attempts < 1000:
        temp_nogo_indices = sorted(random.sample(eligible_indices, num_nogo_p + num_nogo_r))
        is_consecutive = any(temp_nogo_indices[i+1] == temp_nogo_indices[i] + 1 for i in range(len(temp_nogo_indices) - 1))
        if not is_consecutive:
            return temp_nogo_indices
        attempts += 1
    
    # Final failure if non-consecutive trials cannot be found
    raise RuntimeError("Could not find a valid non-consecutive no-go trial distribution after all attempts. "
                       "Try reducing the number of no-go trials per block to avoid this problem.")