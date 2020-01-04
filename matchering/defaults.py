import math


class LimiterConfig:
    def __init__(
            self
    ):
        pass


class MainConfig:
    def __init__(
            self,
            internal_sample_rate=44100,
            max_length=15 * 60,
            threshold=(2**15 - 61) / 2**15,
            min_value=1e-6,
            time_area=15,
            fft_size=4096,
            lin_log_oversample=4,
            peak_compensation_steps=5,
            temp_folder=None,
            limiter=LimiterConfig()
    ):
        assert internal_sample_rate == 44100
        self.internal_sample_rate = internal_sample_rate

        assert max_length > 0
        assert max_length > fft_size / internal_sample_rate
        self.max_length = max_length

        assert threshold > min_value
        assert threshold < 1
        self.threshold = threshold

        assert min_value > 0
        assert min_value < 0.1
        self.min_value = min_value

        assert time_area > 0
        assert time_area > fft_size / internal_sample_rate
        assert time_area < max_length
        self.time_area = time_area

        assert fft_size > 1
        assert math.log2(fft_size).is_integer()
        self.fft_size = fft_size

        assert lin_log_oversample > 0
        assert isinstance(lin_log_oversample, int)
        self.lin_log_oversample = lin_log_oversample

        assert peak_compensation_steps >= 0
        assert isinstance(peak_compensation_steps, int)
        self.peak_compensation_steps = peak_compensation_steps

        assert temp_folder is None or isinstance(temp_folder, str)
        self.temp_folder = temp_folder

        assert isinstance(limiter, LimiterConfig)
        self.limiter = limiter
