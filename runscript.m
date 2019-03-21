% Matchering DSP Module Runscript by Wokashi RG (ex. SOUND.TOOLS)
% https://github.com/wokashi-rg
%
% Folder variables, you need to leave '\' in the end of all folder variables!
% Workspace folder
pathWorkspace = 'C:\matchering\workspace\';
% Target file
fileTarget = 'target.wav';
% Reference file
fileReference = 'reference.wav';
% Temp folder
pathTemp = 'C:\matchering\temp\';
% Folder with mrswatson64.exe and activated brickwall limiter VST DLL
% mrswatson64.exe: https://github.com/teragonaudio/MrsWatson/releases
% Good brickwall limiter: Voxengo Elephant - https://www.voxengo.com/product/elephant/ - this limiter is tested with this script and work very well, we can not guarantee the correct processing (for e.g. latency compensation) with another limiter
% You may leave this variable empty, and you will get matched but not limited version of track (only 32-bit WAV), just process it with any brickwall limiter in your DAW
% Otherwise you will get matched and limited 24-bit and 16-bit WAVs
%pathBin = 'C:\matchering\bin\';
pathBin = '';
% Activated brickwall limiter VST DLL file (not used if pathBin is empty)
fileBrickwallLimiter = 'Elephant.dll';
%
% DSP variables
% Max track length (in minutes)
maxLength = 15;
% Max lenght of analyzed part (in seconds)
timeArea = 15; % 8 bars of 128 bpm
% FFT Size (in samples) need to be a 2^n - 1024, 2048, 4096, 8192, etc.
fftSize = 4096;
% Linear to log10 oversampling coefficient: x1, x2, x3 x4, etc.
linLogOversampling = 4;
% Peak compensation steps
peakCompensationSteps = 5;
%
% ----------------------------------------------------------------

status = matchering(pathWorkspace, fileTarget, fileReference, pathTemp, pathBin, fileBrickwallLimiter, maxLength, timeArea, fftSize, linLogOversampling, peakCompensationSteps);
disp(['Script ended with status ', num2str(status), '.'])

close all;
clear;
