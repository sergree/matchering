import { create } from 'zustand';

interface CompressorParams {
  threshold: number;
  ratio: number;
  attack: number;
  release: number;
}

interface StereoParams {
  width: number;
  rotation: number;
  balance: number;
}

interface LimiterParams {
  threshold: number;
  release: number;
}

interface ProcessingState {
  isEnabled: boolean;
  eqGains: number[];
  compressorParams: CompressorParams;
  stereoParams: StereoParams;
  limiterParams: LimiterParams;
  toggleEnabled: (enabled: boolean) => void;
  updateEqGains: (index: number, value: number) => void;
  updateCompressorParams: (params: Partial<CompressorParams>) => void;
  updateStereoParams: (params: Partial<StereoParams>) => void;
  updateLimiterParams: (params: Partial<LimiterParams>) => void;
}

export const useProcessingStore = create<ProcessingState>((set) => ({
  isEnabled: false,
  eqGains: Array(10).fill(0),  // 10-band EQ
  compressorParams: {
    threshold: -20,
    ratio: 2,
    attack: 10,
    release: 100,
  },
  stereoParams: {
    width: 1,
    rotation: 0,
    balance: 0,
  },
  limiterParams: {
    threshold: -0.1,
    release: 50,
  },

  toggleEnabled: (enabled: boolean) =>
    set({ isEnabled: enabled }),

  updateEqGains: (index: number, value: number) =>
    set((state) => ({
      eqGains: state.eqGains.map((gain, i) =>
        i === index ? value : gain
      ),
    })),

  updateCompressorParams: (params: Partial<CompressorParams>) =>
    set((state) => ({
      compressorParams: {
        ...state.compressorParams,
        ...params,
      },
    })),

  updateStereoParams: (params: Partial<StereoParams>) =>
    set((state) => ({
      stereoParams: {
        ...state.stereoParams,
        ...params,
      },
    })),

  updateLimiterParams: (params: Partial<LimiterParams>) =>
    set((state) => ({
      limiterParams: {
        ...state.limiterParams,
        ...params,
      },
    })),
}));