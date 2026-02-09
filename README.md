# Alternating Serial Reaction Time (ASRT) Task (PsychoPy)

This repository contains a Python-based psychological experiment developed using **PsychoPy** that implements a modified **Alternating Serial Reaction Time (ASRT)** task. The experiment is designed to study implicit sequence learning while monitoring attentional states through **No-Go trials** and **Mind-Wandering (MW) probes**.

---

## Project overview

The task requires participants to respond to target images (a "Dog") appearing in one of four circles while withholding responses to "No-Go" images (a "Cat"). The sequence of appearances alternates between a predetermined pattern and random locations to track learning over time.

### Key features
* **Implicit learning:** The task utilizes a pattern-random alternating sequence to assess implicit learning.
* **Attentional sampling:** Integrated mind-wandering probes periodically interrupt the task to collect subjective focus ratings.
* **Hardware integration:** Supports **Riponda** response boxes (Cedrus) and serial port triggers for synchronization with external devices like EEG.
* **Multilingual support:** Configurable text for multiple languages (English, Spanish, and Hungarian) via external `.ini` files.

---

## Configuration options (`experiment_settings.ini`)

The experiment is controlled by an initialization file that allows researchers to modify the task structure without changing the source code.

### [Experiment] Section
* **num_trials:** The total number of trials within a single block.
* **pattern_sequence:** The base sequence used for the pattern trials.
* **num_blocks:** The total number of blocks in the experiment.
* **interference_epoch_enabled:** If set to True, the pattern sequence is reversed during a specific epoch to test interference.
* **interference_epoch_num:** Determines which epoch (group of blocks) triggers the interference sequence.
* **no_go_trials_enabled:** Toggles whether "No-Go" trials are active.
* **num_no_go_trials:** The quantity of no-go trials included in each block.
* **mw_testing_involved:** Enables the 4-question mind-wandering probes throughout the session.
* **run_quiz_if_mw_enabled:** Determines if a comprehension quiz is shown before the task to ensure participants understand the probe definitions.
* **isi_duration_s:** The duration of the blank screen (Inter-Stimulus Interval) between trials in seconds.
* **nogo_trial_duration_s:** The display time for a no-go stimulus.
* **feedback_enabled:** Toggles the performance summary screen (Accuracy and Mean RT) after each block.
* **response_keys_list:** The physical keyboard keys mapped to the four stimulus positions.
* **target_image_filename:** The image file path for the primary "Go" target.
* **nogo_image_filename:** The image file path for the "No-Go" target.
* **riponda_enabled:** Toggles support for the Riponda response box.
* **riponda_port:** The COM port assigned to the Riponda hardware.
* **riponda_baudrate:** The communication speed for the Riponda device.
* **riponda_keys_list:** The specific characters or codes sent by the response box keys.
* **background_color:** Background color.
* **foreground_color:** Foreground (text color).


### [Practice] Section
* **practice_enabled:** Toggles the inclusion of training blocks before the main task.
* **num_practice_blocks:** The number of blocks used for participant training.

---

## Logged data output

The experiment creates a `data` folder and saves trial-by-trial information in a unique CSV file for each participant.

| Variable | Description |
| :--- | :--- |
| **participant** | The identification number assigned to the individual. |
| **session** | The session index for the current run. |
| **block_number** | Identifies the current block in the experiment. |
| **trial_number** | The total cumulative trial count across the session. |
| **trial_in_block_num** | Position of the trial within its specific block. |
| **trial_type** | Denotes if the trial was pattern-based (P) or random (R). |
| **triplet_type** | A code indicating the frequency of the trial sequence (e.g., High, Low, Trill, Repetition). |
| **sequence_used** | The specific pattern applied during the session. |
| **stimulus_position_num** | Records which of the four locations displayed the target. |
| **rt_non_cumulative_s** | Reaction time from the start of the current stimulus. |
| **rt_cumulative_s** | Reaction time measured since the stimulus onset. |
| **correct_key_pressed** | The required key for a correct response. |
| **response_key_pressed** | The key actually pressed by the participant. |
| **correct_response** | Boolean indicator of whether the response was correct. |
| **is_nogo** | Identifies trials where a response was meant to be withheld. |
| **is_practice** | Distinguishes between training and experimental tasks. |
| **epoch** | Groups blocks to help analyze learning stages over time. |
| **is_first_response** | Defines if keypress is first response attempt or not. (1 - yes, 0 -no) |
| **mind_wandering_rating_1-4** | Subjective ratings from the periodic focus probes. |

---

## Installation and usage

1. **Verify settings:** Open `experiment_settings.ini` to configure your experiment.
2. **Run experiment:** Launch `asrt.py` using a Python environment with PsychoPy installed.
3. **Session info:** Enter participant number (integer) and select the language in the GUI prompt (en - English, es - Spanish, hu - Hungarian).
4. **Follow prompts:** The participant will be guided through instructions, an optional quiz, and practice blocks before the main task begins.

## Performance fix: COM port latency

If your reaction time (RT) data shows "staircase" patterns or 16ms jumps, you must adjust the Windows Serial Driver settings to ensure millisecond precision.

### Steps to fix:
1. **Open Device Manager**: Right-click Start and select **Device Manager**.
2. **Find COM Port**: Expand **Ports (COM & LPT)**, right-click your device (e.g., USB Serial Port), and select **Properties**.
3. **Advanced Settings**: Go to the **Port Settings** tab and click the **Advanced** button.
4. **Set Latency to 1ms**: Change the **Latency Timer (msec)** from 16 to **1**.
5. **Save**: Click **OK** on all windows and restart your script.

**Why this works**: The default 16ms setting buffers response data before sending it to Python. Reducing this to 1ms allows PsychoPy to "see" the button press immediately, resulting in a smooth and accurate RT distribution.

## ASRT data analysis pipeline

This repository also includes a comprehensive **R-based analysis pipeline** designed to process the collected data. The pipeline automates the workflow from raw data aggregation to statistical analysis, ensuring consistent and reproducible results for sequence learning experiments.

The `asrt_analysis.ipynb` notebook performs the following key functions:
1. **Data aggregation**: Automatically detects and merges participant CSV files.
2. **Preprocessing**: Cleans data by filtering non-learning trials.
3. **Outlier removal**: Applies robust statistical filtering (MAD) and absolute thresholds to remove outliers.
4. **Visualization**: Generates distribution plots to assess normality and statistical learning.
5. **Statistical analysis**: Runs ANOVA and Linear Mixed Models to quantify learning effects.

## 🛠 Prerequisites

To run this analysis, you need an **R** environment (e.g., RStudio, Jupyter Notebook with IRKernel). Ensure the following libraries are installed:

```r
install.packages(c("ggplot2", "readr", "lme4", "afex", "dplyr", "tidyr", "moments"))