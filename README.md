# Alternating Serial Reaction Time (ASRT) Task (PsychoPy)

This repository contains a Python-based psychological experiment developed using **PsychoPy** that implements an **Alternating Serial Reaction Time (ASRT)** task. The experiment is designed to study implicit sequence learning through a pattern-random alternating sequence.

---

## Project overview

The task requires participants to respond to target images appearing in one of four circles. The locations of these images alternate between a predetermined pattern and random locations, allowing researchers to track the acquisition of implicit knowledge over time.

### Key features
1. **Task Structure:** The experiment consists of 30 blocks, each containing 80 trials.
2. **Timing:** An Response-to-stimulus Interval (RSI) of 0.120 seconds is set between trials.
3. **Implicit learning:** Utilizes a pattern-random alternating sequence to assess learning.
4. **Hardware Integration:** Configured for Cedrus Riponda response boxes (COM5, 115200 baud) and standard keyboard input.
5. **Feedback:** Participants receive performance summaries (Accuracy and Mean RT) after each block, with a mandatory 6-second wait before proceeding.

---

## Configuration options (`experiment_settings.ini`)

The experiment is controlled by an initialization file that allows researchers to modify the task structure without changing the source code. The variables below are organized exactly as they appear in the configuration file.

### [Experiment]

| Variable | Description | Current Value |
| :--- | :--- | :--- |
| **num_trials** | The total number of trials within a single block. | 80 |
| **num_blocks** | The total number of blocks in the experiment. | 30 |
| **interference_epoch_enabled** | If set to True, the pattern sequence is reversed during a specific epoch to test interference. | False |
| **interference_epoch_num** | Determines which epoch (group of blocks) triggers the interference sequence. | 1 |
| **isi_duration_s** | The duration of the blank screen (Inter-Stimulus Interval) between trials in seconds. | 0.120 |
| **feedback_enabled** | Toggles the performance summary screen (Accuracy and Mean RT) after each block. | True |
| **mandatory_wait_before_next_block_s** | Mandatory wait time before proceeding to the next block in seconds. | 6.0 |
| **mw_testing_involved** | Enables the 4-question mind-wandering probes throughout the session. | False |
| **run_quiz_if_mw_enabled** | Determines if a comprehension quiz is shown before the task to ensure participants understand the probe definitions. | False |
| **no_go_trials_enabled** | Toggles whether "No-Go" trials are active. | False |
| **num_no_go_trials** | The quantity of no-go trials included in each block. | 0 |
| **nogo_trial_duration_s** | The display time for a no-go stimulus. | 1.0 |
| **target_image_filename** | The image file path for the primary "Go" target. | images/target_image.png |
| **nogo_image_filename** | The image file path for the "No-Go" target. | images/nogo_image.png |
| **background_color** | Background color. | black |
| **foreground_color** | Foreground (text color). | white |
| **response_keys_list** | The physical keyboard keys mapped to the four stimulus positions. | s, f, j, l |
| **riponda_enabled** | Toggles support for the Riponda response box. | True |
| **riponda_port** | The COM port assigned to the Riponda hardware. | COM5 |
| **riponda_baudrate** | The communication speed for the Riponda device. | 115200 |
| **riponda_keys_list** | The specific characters or codes sent by the response box keys. | '1', '2', '3', '4' |

### [Practice]

| Variable | Description | Current Value |
| :--- | :--- | :--- |
| **practice_enabled** | Toggles the inclusion of training blocks before the main task. | False |
| **num_practice_blocks** | The number of blocks used for participant training. | 0 |

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
4. **Visualization**: Generates plots to assess normality and statistical learning.
5. **Statistical analysis**: Runs ANOVA and Linear Mixed Models to quantify learning effects.

### Prerequisites

To run this analysis, you need an **R** environment (e.g., RStudio, Jupyter Notebook with IRKernel). Ensure the following libraries are installed:

```r
install.packages(c("ggplot2", "readr", "lme4", "afex", "dplyr", "tidyr", "moments"))