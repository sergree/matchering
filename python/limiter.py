import soundfile as sf
from resampy import resample
from scipy import signal, interpolate
import numpy as np
import math

MAXIMUM_VALUE = 0.998138427734375  # (2 ** 15 - 61) / 2 ** 15


def flip(input):
    return 1. - input


def ms_to_samples(value, sample_rate):
    return int(sample_rate * value * 1e-3)


def make_odd(value):
    return value + 1 if not value & 1 else value


def sliding_window(input, window_size, mode='attack'):
    if mode == 'attack':
        # Attack mode
        window_size = make_odd(window_size)
        pad_width = (window_size - 1, window_size - 1)
        shape = len(input), 2 * window_size - 1
    else:
        # Hold mode
        pad_width = (window_size - 1, 0)
        shape = len(input), window_size
    
    output = np.pad(
        input, 
        pad_width, 
        'constant', 
        constant_values=0
    )
    output = np.lib.stride_tricks.as_strided(
        output, 
        shape, 
        output.strides * 2
    )
    
    return output.max(1)


def process_attack(
    input, 
    sample_rate, 
    attack,
):
    
    attack = ms_to_samples(attack, sample_rate)
    input_len = input.shape[0]
    
    slided_input = sliding_window(input, attack, mode='attack')
    
    coef = math.exp(-2 / attack)
    b = [1 - coef]
    a = [1, -coef]
    output = signal.filtfilt(b, a, slided_input)
    
    return output, slided_input


def process_release(
    input, 
    sample_rate, 
    hold,
    release, 
):
    hold = ms_to_samples(hold, sample_rate)
    input_len = input.shape[0]
    
    slided_input = sliding_window(input, hold, mode='hold')
    
    b, a = signal.butter(1, 7, fs=sample_rate)
    hold_output = signal.lfilter(b, a, slided_input)
    
    b, a = signal.butter(1, 800 / release, fs=sample_rate)
    release_output = signal.lfilter(b, a, np.maximum(slided_input, hold_output))
    
    return np.maximum(hold_output, release_output)


def simple_limiter(
    input, 
    sample_rate, 
    threshold=MAXIMUM_VALUE,
    attack=1,
    release=3000,
    hold=1
):
    """
    Simple Limiter
    """
    rectified = np.abs(input).max(1)
    rectified[rectified <= threshold] = threshold
    rectified /= threshold
    gain_hard_clip = flip(1. / rectified)
    
    gain_attack, gain_hard_clip_slided = process_attack(np.copy(gain_hard_clip), sample_rate, attack)
    gain_release = process_release(np.copy(gain_hard_clip_slided), sample_rate, hold, release)
    
    gain = flip(np.maximum.reduce([gain_hard_clip, gain_attack, gain_release]))
    
    return input * gain[:, None]
