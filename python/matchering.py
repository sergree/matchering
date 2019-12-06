from scipy import signal, interpolate
import numpy as np
import soundfile as sf
from resampy import resample
from time import time
import os
import argparse

LIMITED_MAXIMUM_POINT = 0.998138427734375
MINIMUM_FLOOR = 1e-6


def _smooth(y, span):
    M = int(len(y) * span)
    if M & 1:
        pass
    else:
        M += 1
    cumsum_y = np.cumsum(y)
    mid_out = cumsum_y[M:] - cumsum_y[:-M]
    r = np.arange(1, M - 1, 2)
    start_out = cumsum_y[:M - 1:2] / r
    stop_out = np.cumsum(y[:-M:-1])[::2] / r
    return np.concatenate((start_out, mid_out, stop_out[::-1]))


def _get_fir(target_parts, ref_parts, sr, nfft, lin_log_oversample):
    *_, specs = signal.stft(target_parts, sr, window='boxcar', nperseg=nfft, noverlap=0, boundary=None,
                            padded=False)
    target_avg_fft = np.abs(specs).mean((0, 2))

    *_, specs = signal.stft(ref_parts, sr, window='boxcar', nperseg=nfft, noverlap=0, boundary=None,
                            padded=False)
    ref_avg_fft = np.abs(specs).mean((0, 2))

    np.maximum(1e-6, target_avg_fft, out=target_avg_fft)
    matching_fft = ref_avg_fft / target_avg_fft

    del specs

    grid_linear = sr * 0.5 * np.linspace(0, 1, nfft // 2 + 1)
    grid_logarithmic = sr * 0.5 * np.logspace(np.log10(4 / nfft), 0, nfft * 0.5 * (lin_log_oversample + 1))

    f = interpolate.interp1d(grid_linear, matching_fft, 'cubic')
    matching_fft_log = f(grid_logarithmic)

    # use moving average filter, may re-implement 'loess' method in future
    matching_fft_log_filtered = _smooth(matching_fft_log, 0.075)
    f = interpolate.interp1d(grid_logarithmic, matching_fft_log_filtered, 'cubic')
    matching_fft_filtered = f(grid_linear)

    matching_fft_filtered[0] = 0
    matching_fft_filtered[1] = matching_fft[1]
    fir = np.fft.irfft(matching_fft_filtered)
    fir = np.fft.ifftshift(fir) * signal.hanning(len(fir))
    return fir


def main(target, ref, area_size, sr, nfft, lin_log_oversample, peak_compensation_steps, output_filename):
    print('--------------------------------\n'
          'Stage 0 - Normalizing Reference')

    ref_max = np.abs(ref).max()
    final_amp_coef = 1
    if ref_max >= LIMITED_MAXIMUM_POINT:
        print('Reference is not changed. No final amplitude coefficient')
    else:
        final_amp_coef = max(1e-6, ref_max / LIMITED_MAXIMUM_POINT)
        ref /= final_amp_coef
        print('Reference is normalized. Final aplitude coefficient for target audio will be:', final_amp_coef)

    print('Stage 0 completed\n'
          '--------------------------------\n'
          'Stage 1 - Matching RMS')

    print('Calculating mid channel of target...')
    target_mid = target.mean(1)
    print('Calculating mid channel of reference...')
    ref_mid = ref.mean(1)
    print('Calculating side channel of target...')
    target_side = 0.5 * (target[:, 0] - target[:, 1])
    print('Calculating side channel of reference...')
    ref_side = np.ascontiguousarray(ref[:, 0])
    ref_side -= ref[:, 1]
    ref_side *= 0.5

    target_size = target.shape[0]
    ref_size = ref.shape[0]
    target_divisions = int(target_size / area_size) + 1
    print('Target will be didived into ', target_divisions, ' parts')
    ref_divisions = int(ref_size / area_size) + 1
    print('Reference will be didived into ', ref_divisions, ' parts')

    target_part_size = int(target_size / target_divisions)
    print('One part of target is ', target_part_size, ' samples or ', target_part_size / sr, ' seconds')
    ref_part_size = int(ref_size / ref_divisions)
    print('One part of reference is ', ref_part_size, ' samples or ', ref_part_size / sr, ' seconds')

    def batch_rms(x, part):
        y = np.squeeze(x[:, None, :] @ x[..., None])
        y /= part
        np.sqrt(y, out=y)
        return y

    unfolded_target_mid = target_mid[:target_part_size * target_divisions].reshape(-1, target_part_size)
    unfolded_target_side = target_side[:target_part_size * target_divisions].reshape(-1, target_part_size)
    unfolded_ref_mid = ref_mid[:ref_part_size * ref_divisions].reshape(-1, ref_part_size)
    unfolded_ref_side = ref_side[:ref_part_size * ref_divisions].reshape(-1, ref_part_size)

    print('Calculating RMSes of target parts...')
    target_rmses = batch_rms(unfolded_target_mid, target_part_size)

    print('Calculating RMSes of target parts...')
    ref_rmses = batch_rms(unfolded_ref_mid, ref_part_size)

    target_avg_rms = np.sqrt(target_rmses @ target_rmses / target_divisions)
    ref_avg_rms = np.sqrt(ref_rmses @ ref_rmses / ref_divisions)

    print('Extracting parts from target audio with RMS more than average', target_avg_rms, '...')

    target_analyze_part_idxs = np.where(target_rmses >= target_avg_rms)
    target_mid_analyze_parts = unfolded_target_mid[target_analyze_part_idxs]
    target_side_analyze_parts = unfolded_target_side[target_analyze_part_idxs]
    target_analyze_rmses = target_rmses[target_analyze_part_idxs]

    print('Extracting parts from reference audio with RMS more than average', ref_avg_rms, '...')

    ref_analyze_part_idxs = np.where(ref_rmses >= ref_avg_rms)
    ref_mid_analyze_parts = unfolded_ref_mid[ref_analyze_part_idxs]
    ref_side_analyze_parts = unfolded_ref_side[ref_analyze_part_idxs]
    ref_analyze_rmses = ref_rmses[ref_analyze_part_idxs]

    target_match_rms = np.sqrt(target_analyze_rmses @ target_analyze_rmses / len(target_analyze_rmses))
    target_match_rms = max(1e-6, target_match_rms)
    ref_match_rms = np.sqrt(ref_analyze_rmses @ ref_analyze_rmses / len(ref_analyze_rmses))

    rms_coeff = ref_match_rms / target_match_rms
    print('The RMS coefficient is:', rms_coeff)

    print('Modifying amplitudes of target...')

    # output_stage1 = np.vstack((target_mid, target_side)).T * rms_coeff
    output_mid = target_mid * rms_coeff
    output_side = target_side * rms_coeff
    print('Modifying amplitudes of extracted target parts...')
    target_mid_analyze_parts *= rms_coeff
    target_side_analyze_parts *= rms_coeff

    print('Stage 1 completed\n'
          '--------------------------------\n'
          'Stage 2 - Matching FR')

    print('Calculating mid FIR for matching EQ...')
    mid_fir = _get_fir(target_mid_analyze_parts, ref_mid_analyze_parts, sr, nfft, lin_log_oversample)

    print('Calculating side FIR for matching EQ...')
    side_fir = _get_fir(target_side_analyze_parts, ref_side_analyze_parts, sr, nfft, lin_log_oversample)

    print('Convolving target with calculated FIRs...')
    a = time()

    output_mid = signal.fftconvolve(output_mid, mid_fir, 'same')
    output_side = signal.fftconvolve(output_side, side_fir, 'same')
    print('Done convolution in ', time() - a, ' sec.')
    print('Cutting convolution edges and converting MS to LR...')
    output_0 = output_mid + output_side
    output_1 = output_mid - output_side
    tmp_output = np.vstack((output_0, output_1)).T

    print('Stage 2 completed\n'
          '--------------------------------\n'
          'Stage 3 - RMS Correction')

    # reuse output_mid from stage 2

    for p in range(peak_compensation_steps - 1):
        print('Applying peak compensation #', p + 1, ': simple algorithm...')
        mid_limited = np.clip(output_mid, -1, 1)

        unfolded_mid_limited = mid_limited[:target_part_size * target_divisions].reshape(-1, target_part_size)
        limited_rmses = batch_rms(unfolded_mid_limited, target_part_size)

        limited_avg_rms = np.sqrt(limited_rmses @ limited_rmses / target_divisions)
        analyze_rmses = limited_rmses[np.where(limited_rmses > limited_avg_rms)]
        analyze_avg_rms = np.sqrt(analyze_rmses @ analyze_rmses / len(analyze_rmses))
        print('Current average RMS value in loudest parts is ', analyze_avg_rms)

        analyze_avg_rms = max(1e-6, analyze_avg_rms)
        rms_coeff = ref_match_rms / analyze_avg_rms

        if p < peak_compensation_steps - 2:
            print('The RMS correction coefficient #', p + 1, ' is: ', rms_coeff, '. Modifying amplitudes...')
        else:
            print('The final RMS correction coefficient is: ', rms_coeff, '. Modifying amplitudes of the target...')
        output_mid *= rms_coeff
        tmp_output *= rms_coeff

    print('Stage 3 completed\n'
          '--------------------------------\n'
          'Fianl Stage - Export')

    if final_amp_coef != 1:
        print('Modifying amplitudes with final aplitude coefficient: ', final_amp_coef, '...')
        final_output = tmp_output * final_amp_coef
    else:
        final_output = tmp_output

    pathdir, f = os.path.split(output_filename)
    f = '[Matchered 32-bit NO LIMITING] ' + f
    final_output_name = os.path.join(pathdir, f)
    print('Saving modified target audio in WAV 32bit to ', final_output_name, '...')
    sf.write(final_output_name, final_output, sr, 'FLOAT')
    print(f, ' saved')

    print('Final stage completed')