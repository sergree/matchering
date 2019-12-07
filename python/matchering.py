from scipy import signal, interpolate
import numpy as np
import soundfile as sf
from resampy import resample
from time import time
import os
import math
import argparse

LIMITED_MAXIMUM_POINT = 0.998138427734375
MINIMUM_FLOOR = 1e-6


def _to_db(x):
    return str(20 * math.log10(x)) + ' db'


def _smooth(y, span):
    M = int(len(y) * span)
    if M & 1:
        pass
    else:
        M += 1
    cumsum_y = np.cumsum(np.pad(y, (1, 0), 'constant', constant_values=0))
    mid_out = (cumsum_y[M:] - cumsum_y[:-M]) / M
    r = np.arange(1, M - 1, 2)
    start_out = cumsum_y[1:M:2] / r
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
    f = interpolate.interp1d(grid_logarithmic, matching_fft_log_filtered, 'cubic', fill_value='extrapolate')
    matching_fft_filtered = f(grid_linear)

    matching_fft_filtered[0] = 0
    matching_fft_filtered[1] = matching_fft[1]
    fir = np.fft.irfft(matching_fft_filtered)
    fir = np.fft.ifftshift(fir) * signal.windows.hann(len(fir))
    return fir


def main(target, ref, area_size, sr, nfft, lin_log_oversample, peak_compensation_steps, output_dir, output_filename):
    print('--------------------------------\n'
          'Stage 0 - Normalizing Reference')

    ref_max = np.abs(ref).max()
    final_amp_coef = 1
    if ref_max >= LIMITED_MAXIMUM_POINT:
        print('Reference is not changed. No final amplitude coefficient')
    else:
        final_amp_coef = max(1e-6, ref_max / LIMITED_MAXIMUM_POINT)
        ref /= final_amp_coef
        print('Reference is normalized. Final aplitude coefficient for target audio will be:', _to_db(final_amp_coef))

    print('Stage 0 completed\n'
          '--------------------------------\n'
          'Stage 1 - Matching RMS')

    print('Calculating mid channel of target...')
    target[:, 0] += target[:, 1]
    target[:, 0] *= 0.5
    target_mid = np.ascontiguousarray(target[:, 0])
    print('Calculating mid channel of reference...')
    ref[:, 0] += ref[:, 1]
    ref[:, 0] *= 0.5
    ref_mid = np.ascontiguousarray(ref[:, 0])
    print('Calculating side channel of target...')
    target[:, 0] -= target[:, 1]
    target_side = np.ascontiguousarray(target[:, 0])
    print('Calculating side channel of reference...')
    ref[:, 0] -= ref[:, 1]
    ref_side = np.ascontiguousarray(ref[:, 0])

    target_size = target.shape[0]
    ref_size = ref.shape[0]
    target_divisions = int(target_size / area_size) + 1
    print('Target will be didived into ', target_divisions, ' parts')
    ref_divisions = int(ref_size / area_size) + 1
    print('Reference will be didived into ', ref_divisions, ' parts')

    del target, ref
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

    print('Extracting parts from target audio with RMS more than average', _to_db(target_avg_rms), '...')

    target_analyze_part_idxs = np.where(target_rmses >= target_avg_rms)
    target_mid_analyze_parts = unfolded_target_mid[target_analyze_part_idxs]
    target_side_analyze_parts = unfolded_target_side[target_analyze_part_idxs]
    target_analyze_rmses = target_rmses[target_analyze_part_idxs]

    print('Extracting parts from reference audio with RMS more than average', _to_db(ref_avg_rms), '...')

    ref_analyze_part_idxs = np.where(ref_rmses >= ref_avg_rms)
    ref_mid_analyze_parts = unfolded_ref_mid[ref_analyze_part_idxs]
    ref_side_analyze_parts = unfolded_ref_side[ref_analyze_part_idxs]
    ref_analyze_rmses = ref_rmses[ref_analyze_part_idxs]

    target_match_rms = np.sqrt(target_analyze_rmses @ target_analyze_rmses / len(target_analyze_rmses))
    target_match_rms = max(1e-6, target_match_rms)
    ref_match_rms = np.sqrt(ref_analyze_rmses @ ref_analyze_rmses / len(ref_analyze_rmses))

    rms_coeff = ref_match_rms / target_match_rms
    print('The RMS coefficient is:', _to_db(rms_coeff))

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
    tmp_output = np.vstack((output_mid + output_side, output_mid - output_side)).T

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
        print('Current average RMS value in loudest parts is ', _to_db(analyze_avg_rms))

        analyze_avg_rms = max(1e-6, analyze_avg_rms)
        rms_coeff = ref_match_rms / analyze_avg_rms

        if p < peak_compensation_steps - 2:
            print('The RMS correction coefficient #', p + 1, ' is: ', _to_db(rms_coeff), '. Modifying amplitudes...')
        else:
            print('The final RMS correction coefficient is: ', _to_db(rms_coeff),
                  '. Modifying amplitudes of the target...')
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

    normalize_scale = np.abs(final_output).max()
    final_output /= normalize_scale

    print("Recommend adjust amplitude about", _to_db(normalize_scale))

    # pathdir, f = os.path.split(output_filename)
    f = '[Matchered 32-bit NO LIMITING]' + output_filename
    final_output_name = os.path.join(output_dir, f)
    print('Saving modified target audio in WAV 32bit to ', final_output_name, '...')
    sf.write(final_output_name, final_output, sr, 'FLOAT')
    print(f, ' saved')

    print('Final stage completed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage='Matchering DSP Module 0.86 by Wokashi RG (ex. SOUND.TOOLS)\n'
                                           'https://github.com/SOUNDTOOL\n'
                                           'All non-44100 audio will be resampled to 44100 for now \n'
                                           'Only stereo and mono supported for now')
    parser.add_argument('target', type=str, help='inpurt target file, must be in .wav format')
    parser.add_argument('reference', type=str, help='inpurt reference file, must be in .wav format')
    parser.add_argument('--output_dir', type=str, default='./',
                        help='directory to put the output file. default to working directory')
    parser.add_argument('--time_area', type=float, default=15, help='Max length of analyzed part (in seconds)')
    parser.add_argument('--fft_size', type=int, default=4096)
    parser.add_argument('--lin_log_oversample', type=int, default=4,
                        help='Linear to log10 oversampling coefficient: x1, x2, x3 x4, etc.')
    parser.add_argument('--peak_compensation_steps', type=int, default=5)

    args = parser.parse_args()

    fixed_sr = 44100
    max_length = 15

    print('Matchering DSP Module 0.86 by Wokashi RG (ex. SOUND.TOOLS)\n'
          '----------------------------------------------------------------')
    print('Target file:', args.target)
    print('Reference file:', args.reference)

    print('Loading target ...')
    try:
        target, target_sr = sf.read(args.target, always_2d=True)
        print('Target file is loaded')
    except:
        print('ERROR: Unknown audio stream in target file')
        exit(1)

    print('Loading reference ...')
    try:
        ref, ref_sr = sf.read(args.reference, always_2d=True)
        print('reference file is loaded')
    except:
        print('ERROR: Unknown audio stream in reference file')
        exit(1)

    if target_sr != fixed_sr:
        print('Target track is not 44100! Resampling...')
        target = resample(target, target_sr, 44100, axis=0)

    if ref_sr != fixed_sr:
        print('Reference track is not 44100! Resampling...')
        ref = resample(ref, ref_sr, 44100, axis=0)

    print('Size of target WAV: ', target.shape[0], 'samples or ', target.shape[0] / fixed_sr, ' seconds')
    if target.shape[0] > max_length * 60 * fixed_sr:
        print('ERROR: Target track length is more than maximum (', max_length, ' minutes)')
        exit(1)

    if target.shape[0] < args.fft_size:
        print('ERROR: Target track length is less than minimum (', args.fft_size, ' samples)')
        exit(1)

    print('Size of reference WAV: ', ref.shape[0], 'samples or ', ref.shape[0] / fixed_sr, ' seconds')
    if ref.shape[0] > max_length * 60 * fixed_sr:
        print('ERROR: reference track length is more than maximum (', max_length, ' minutes)')
        exit(1)

    if ref.shape[0] < args.fft_size:
        print('ERROR: reference track length is less than minimum (', args.fft_size, ' samples)')
        exit(1)

    area_size = args.time_area * fixed_sr
    print('Max size of analyzed part: ', area_size, ' samples or ', args.time_area, ' seconds')

    if target.shape[1] == 1:
        print('Target audio is mono. Converting it to stereo...')
        target = np.repeat(target, 2, 1)
    elif target.shape[1] > 2:
        print('ERROR: Target track has more than 2 channels')
        exit(1)

    if ref.shape[1] == 1:
        print('Reference audio is mono. Converting it to stereo...')
        ref = np.repeat(ref, 2, 1)
    elif ref.shape[1] > 2:
        print('ERROR: Reference track has more than 2 channels')
        exit(1)

    target_maximum = np.abs(target).max()
    target_maximum_points = np.count_nonzero(np.logical_or(target == target_maximum, target == - target_maximum))
    ref_maximum = np.abs(ref).max()
    ref_maximum_points = np.count_nonzero(np.logical_or(ref == ref_maximum, ref == - ref_maximum))

    if target_maximum_points > 8:
        if target_maximum == 1:
            print(
                'WARNING: Audio clipping detected in the target! It is very recommended to use version without clipping!')
        elif target_maximum_points > 128:
            print(
                'WARNING: Applied limiter detected in the target! It is very recommended to use version without limiter!')

    if ref_maximum_points > 8 and ref_maximum == 1:
        print('INFO: Audio clipping detected in the reference')

    main(target, ref, area_size, fixed_sr, args.fft_size, args.lin_log_oversample, args.peak_compensation_steps,
         args.output_dir, os.path.split(args.target)[1])
