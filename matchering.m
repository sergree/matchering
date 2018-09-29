% Matchering DSP Module 0.86 by SOUND.TOOLS
% https://github.com/SOUNDTOOLS
%
% You need to place mrswatson64.exe and activated brickwall limiter VST DLL in the folder specified in pathBin variable!
%
% All non-44100 audio will be resampled to 44100 for now
% Only stereo and mono supported for now
%
% This module made in procedural style, not OOP, sorry :)
%
% ----------------------------------------------------------------

function currentSessionStatus = matchering(pathWorkspace, fileTarget, fileReference, pathTemp, pathBin, fileBrickwallLimiter, maxLength, timeArea, fftSize, linLogOversampling, peakCompensationSteps)

disp('Matchering DSP Module 0.86 by SOUND.TOOLS')
disp('----------------------------------------------------------------')

currentSessionStatus = 2;

disp(['Target file: ', fileTarget])
disp(['Reference file: ', fileReference])

currentSessionStatus = 3;

filesIsOk = true;

%Loading the target
disp(['Loading target ', pathWorkspace, fileTarget, '...'])
try
    [target, targetSamplingFrequency] = audioread([pathWorkspace, fileTarget]);
    disp('Target file is loaded')
catch
    disp('ERROR: Unknown audio stream in target file')
    filesIsOk = false;
    currentSessionStatus = 31;
end

%Loading the reference
disp(['Loading reference ', pathWorkspace, fileReference, '...'])
try
    [reference, referenceSamplingFrequency] = audioread([pathWorkspace, fileReference]);
    disp('Reference file is loaded')
catch
    if filesIsOk == true
        disp('ERROR: Unknown audio stream in reference file')
        filesIsOk = false;
        currentSessionStatus = 32;
    else
        disp('ERROR: Unknown audio stream in reference file too')
        currentSessionStatus = 30;
    end
end

if filesIsOk == true
    
    % Hard link to 44100!
    if targetSamplingFrequency ~= 44100
        disp('Target track is not 44100! Resampling...')
        target = resample(target, 44100, targetSamplingFrequency);
        targetSamplingFrequency = 44100;
    end
    
    if referenceSamplingFrequency ~= 44100
        disp('Reference track is not 44100! Resampling...')
        reference = resample(reference, 44100, referenceSamplingFrequency);
        referenceSamplingFrequency = 44100;
    end
    
    % Checking length of the target
    maxLengthIsOk = true;
    minLengthIsOk = true;
    targetSize = size(target, 1);
    disp(['Size of target WAV: ', num2str(targetSize) ,' samples or ', num2str(targetSize / targetSamplingFrequency), ' seconds'])
    if targetSize > (double(maxLength) * targetSamplingFrequency * 60)
        disp(['ERROR: Target track length is more than maximum (', num2str(double(maxLength)), ' minutes)'])
        maxLengthIsOk = false;
        currentSessionStatus = 34;
    end
    if targetSize < double(fftSize)
        disp(['ERROR: Target track length is less than minimum (', num2str(double(fftSize)), ' samples)'])
        minLengthIsOk = false;
        currentSessionStatus = 40;
    end
    
    % Checking length of the reference
    referenceSize = size(reference, 1);
    disp(['Size of reference WAV: ', num2str(referenceSize), ' samples or ',num2str(referenceSize/referenceSamplingFrequency), ' seconds'])
    if referenceSize > (double(maxLength) * referenceSamplingFrequency * 60)
        if minLengthIsOk == true
            if maxLengthIsOk == true
                disp(['ERROR: Reference track length is more than maximum (', num2str(double(maxLength)), ' minutes)'])
                maxLengthIsOk = false;
                currentSessionStatus = 35;
            else
                disp(['ERROR: Reference track length is more than maximum (', num2str(double(maxLength)), ' minutes) too'])
                currentSessionStatus = 33;
            end
        else
            disp(['ERROR: Reference track length is more than maximum (', num2str(double(maxLength)),' minutes)'])
            maxLengthIsOk = false;
            currentSessionStatus = 42;
        end
    end
    if referenceSize < double(fftSize)
        if maxLengthIsOk == true
            if minLengthIsOk == true
                disp(['ERROR: Reference track length is less than minimum (', num2str(double(fftSize)), ' samples)'])
                minLengthIsOk = false;
                currentSessionStatus = 41;
            else
                disp(['ERROR: Reference track length is less than minimum (', num2str(double(fftSize)), ' samples) too'])
                currentSessionStatus = 39;
            end
        else
            disp(['ERROR: Reference track length is less than minimum (', num2str(double(fftSize)), ' samples)'])
            minLengthIsOk = false;
            currentSessionStatus = 43;
        end
    end
    
    if maxLengthIsOk == true
        
        if minLengthIsOk == true
            
            areaSize = double(timeArea) * targetSamplingFrequency;
            disp(['Max size of analyzed part: ', num2str(areaSize), ' samples or ', num2str(double(timeArea)), ' seconds'])
            
            % Converting mono to stereo
            if size(target, 2) == 1
                disp('Target audio is mono. Converting it to stereo...')
                target(:, 2) = target(:, 1);
            end
            if size(reference, 2) == 1
                disp('Reference audio is mono. Converting it to stereo...')
                reference(:, 2) = reference(:, 1);
            end
            
            % Determining audio files with more than 2 channels
            channelsIsOk = true;
            if size(target, 2) > 2
                disp('ERROR: Target track has more than 2 channels')
                channelsIsOk = false;
                currentSessionStatus = 37;
            end
            if size(reference, 2) > 2
                if channelsIsOk == true
                    disp('ERROR: Reference track has more than 2 channels')
                    channelsIsOk = false;
                    currentSessionStatus = 38;
                else
                    disp('ERROR: Reference track has more than 2 channels too')
                    currentSessionStatus = 36;
                end
            end
            
            if channelsIsOk == true
                
                % Checking peaks and limiters
                
                targetSameMaximumPoints = sum(target(:) == max(max(abs(target)))) + sum(target(:) == -max(max(abs(target))));
                referenceSameMaximumPoints = sum(reference(:) == max(max(abs(reference)))) + sum(reference(:) == -max(max(abs(reference))));
                
                if targetSameMaximumPoints > 8
                    if max(max(abs(target))) == 1
                        disp('WARNING: Audio clipping detected in the target! It is very recommended to use version without clipping!')
                    else
                        if targetSameMaximumPoints > 128
                            disp('WARNING: Applied limiter detected in the target! It is very recommended to use version without limiter!')
                        end
                    end
                end
                
                if referenceSameMaximumPoints > 8
                    if max(max(abs(reference))) == 1
                        disp('INFO: Audio clipping detected in the reference')
                    end
                end
                
                disp('--------------------------------')
                
                disp('Stage 0 - Normalizing Reference')
                
                currentSessionStatus = 4;
                
                % Stage 0 - Normalizing Reference
                
                LIMITED_MAXIMUM_POINT = 0.998138427734375;
                
                if max(max(abs(reference))) >= LIMITED_MAXIMUM_POINT
                    finalAmplitudeCoefficient = 1;
                    disp('Reference is not changed. No final amplitude coefficient')
                else
                    finalAmplitudeCoefficient = max(max(abs(reference))) / LIMITED_MAXIMUM_POINT;
                    if finalAmplitudeCoefficient < 0.000001
                        finalAmplitudeCoefficient = 0.000001;
                    end
                    reference = reference ./ finalAmplitudeCoefficient;
                    disp(['Reference is normalized. Final aplitude coefficient for target audio will be: ', num2str(finalAmplitudeCoefficient)])
                end
                
                disp('Stage 0 completed')
                
                disp('--------------------------------')
                
                % Stage 1 - Matching RMS
                
                disp('Stage 1 - Matching RMS')
                
                disp('Calculating mid channel of target...');
                targetMid(:) = (target(:, 1) + target(:, 2)) ./ 2;
                
                disp('Calculating mid channel of reference...');
                referenceMid(:) = (reference(:, 1) + reference(:, 2)) ./ 2;
                
                disp('Calculating side channel of target...');
                targetSide(:) = (target(:, 1) - target(:, 2)) ./ 2;
                
                disp('Calculating side channel of reference...');
                referenceSide(:) = (reference(:, 1) - reference(:, 2)) ./ 2;
                
                disp('Unloading original reference from memory...')
                clearvars reference;
                
                targetDivisions = fix(targetSize / areaSize) + 1;
                disp(['Target will be didived into ', num2str(targetDivisions), ' parts'])
                referenceDivisions = fix(referenceSize / areaSize) + 1;
                disp(['Reference will be didived into ', num2str(referenceDivisions), ' parts'])
                
                % Finding sizes of parts
                targetPartSize = fix(targetSize / targetDivisions);
                disp(['One part of target is ', num2str(targetPartSize), ' samples or ', num2str(targetPartSize / targetSamplingFrequency), ' seconds'])
                referencePartSize = fix(referenceSize / referenceDivisions);
                disp(['One part of reference is ', num2str(referencePartSize), ' samples or ', num2str(referencePartSize / referenceSamplingFrequency), ' seconds'])
                
                disp('Calculating RMSes of target parts...');
                targetRmses = zeros(1, targetDivisions);
                for i = 1 : 1 : targetDivisions
                    targetRmses(i) = rms(targetMid( (targetPartSize * (i - 1) + 1) : (targetPartSize * i) ));
                end
                
                disp('Calculating RMSes of reference parts...');
                referenceRmses = zeros(1, referenceDivisions);
                for j = 1 : 1 : referenceDivisions
                    referenceRmses(j) = rms(referenceMid( (referencePartSize * (j - 1) + 1) : (referencePartSize*j) ));
                end
                
                % Average RMSes of mid channels
                targetAverageRms = rms(targetRmses);
                referenceAverageRms = rms(referenceRmses);
                
                disp(['Extracting parts from target audio with RMS more than average ', num2str(targetAverageRms), '...'])
                % May add array preallocation here in future
                j = 1;
                for i = 1 : 1 : targetDivisions
                    if targetRmses(i) >= (targetAverageRms)
                        targetAnalyzedPartNumbers(j) = i;
                        j = j + 1;
                    end
                end
                targetMidAnalyzedPartsTemp = zeros(size(targetAnalyzedPartNumbers, 2), targetPartSize);
                targetSideAnalyzedPartsTemp = zeros(size(targetAnalyzedPartNumbers, 2), targetPartSize);
                for i = 1 : 1 : size(targetAnalyzedPartNumbers, 2)
                    targetMidAnalyzedPartsTemp(i, :) = targetMid( (targetPartSize * (targetAnalyzedPartNumbers(i) - 1) + 1) : (targetPartSize * targetAnalyzedPartNumbers(i)) );
                    targetSideAnalyzedPartsTemp(i, :) = targetSide( (targetPartSize * (targetAnalyzedPartNumbers(i) - 1) + 1) : (targetPartSize * targetAnalyzedPartNumbers(i)) );
                end
                targetAnalyzedRmses = zeros(1, size(targetAnalyzedPartNumbers, 2));
                for i = 1 : 1 : size(targetAnalyzedPartNumbers, 2)
                    targetAnalyzedRmses(i) = targetRmses(targetAnalyzedPartNumbers(i));
                end
                
                disp(['Extracting parts from reference audio with RMS more than average ', num2str(referenceAverageRms), '...'])
                % May add array preallocation here in future
                j = 1;
                for i = 1 : 1 : referenceDivisions
                    if referenceRmses(i) >= (referenceAverageRms)
                        referenceAnalyzedPartNumbers(j) = i;
                        j = j + 1;
                    end
                end
                referenceMidAnalyzedPartsTemp = zeros(size(referenceAnalyzedPartNumbers, 2), referencePartSize);
                referenceSideAnalyzedPartsTemp = zeros(size(referenceAnalyzedPartNumbers, 2), referencePartSize);
                for i = 1 : 1 : size(referenceAnalyzedPartNumbers, 2)
                    referenceMidAnalyzedPartsTemp(i, :) = referenceMid( (referencePartSize * (referenceAnalyzedPartNumbers(i) - 1) + 1) : (referencePartSize * referenceAnalyzedPartNumbers(i)) );
                    referenceSideAnalyzedPartsTemp(i, :) = referenceSide( (referencePartSize * (referenceAnalyzedPartNumbers(i) - 1) + 1) : (referencePartSize * referenceAnalyzedPartNumbers(i)) );
                end
                referenceAnalyzedRmses = zeros(1, size(referenceAnalyzedPartNumbers, 2));
                for i = 1 : 1 : size(referenceAnalyzedPartNumbers, 2)
                    referenceAnalyzedRmses(i) = referenceRmses(referenceAnalyzedPartNumbers(i));
                end
                
                disp('Unloading mid channel of reference from memory...')
                clearvars referenceMid;
                
                disp('Unloading side channel of reference from memory...')
                clearvars referenceSide;
                
                targetMatchingRms = rms(targetAnalyzedRmses);
                if targetMatchingRms < 0.000001
                    targetMatchingRms = 0.000001;
                end
                referenceMatchingRms = rms(referenceAnalyzedRmses);
                
                rmsCoefficient = referenceMatchingRms / targetMatchingRms;
                disp(['The RMS coefficient is: ', num2str(rmsCoefficient)])
                
                disp('Modifying amplitudes of target...')
                outputStage1(:, 1) = targetMid .* rmsCoefficient;  % Left channel of this is mid
                outputStage1(:, 2) = targetSide .* rmsCoefficient; % Right channel of this is side
                disp('Modifying amplitudes of extracted target parts...')
                targetMidAnalyzedParts = targetMidAnalyzedPartsTemp .* rmsCoefficient;
                targetSideAnalyzedParts = targetSideAnalyzedPartsTemp .* rmsCoefficient;
                
                disp('Unloading mid channel of target from memory...')
                clearvars targetMid;
                
                disp('Unloading side channel of target from memory...')
                clearvars targetSide;
                
                disp('Partly cleaning memory...')
                clearvars -except currentSessionStatus outputStage1 finalAmplitudeCoefficient pathWorkspace fileTarget fileReference pathTemp pathBin fileBrickwallLimiter maxLength timeArea fftSize linLogOversampling peakCompensationSteps targetSamplingFrequency targetDivisions targetPartSize targetMidAnalyzedParts targetSideAnalyzedParts referencePartSize referenceMidAnalyzedPartsTemp referenceSideAnalyzedPartsTemp referenceMatchingRms;
                
                disp('Stage 1 completed')
                
                disp('--------------------------------')
                
                % Stage 2 - Matching FR
                
                disp('Stage 2 - Matching FR')
                
                currentSessionStatus = 5;
                
                targetMidFftCount = fix(targetPartSize / double(fftSize));
                targetSideFftCount = targetMidFftCount;
                referenceMidFftCount = fix(referencePartSize / double(fftSize));
                referenceSideFftCount = referenceMidFftCount;
                
                % ---MID---
                
                disp(['Calculating ', num2str(targetMidFftCount * size(targetMidAnalyzedParts, 1)), ' FFTs of target mid...'])
                targetMidAverageFft = zeros(size(targetMidAnalyzedParts, 1), double(fftSize));
                for j = 1 : 1 : size(targetMidAnalyzedParts, 1)
                    targetMidFft = zeros(targetMidFftCount, double(fftSize));
                    for i = 1 : 1 : targetMidFftCount
                        targetMidFft(i, :) = abs(fft(targetMidAnalyzedParts(j, (double(fftSize) * (i - 1) + 1) : (double(fftSize) * i) )));
                    end
                    if size(targetMidFft, 1) == 1
                        targetMidAverageFft(j, :) = targetMidFft;
                    else
                        targetMidAverageFft(j, :) = sum(targetMidFft) ./ targetMidFftCount;
                    end
                    clearvars targetMidFft;
                end
                
                disp(['Calculating ', num2str(referenceMidFftCount * size(referenceMidAnalyzedPartsTemp, 1)), ' FFTs of reference mid...'])
                referenceMidAverageFft = zeros(size(referenceMidAnalyzedPartsTemp, 1), double(fftSize));
                for j = 1 : 1 : size(referenceMidAnalyzedPartsTemp, 1)
                    referenceMidFft = zeros(referenceMidFftCount, double(fftSize));
                    for i = 1 : 1 : referenceMidFftCount
                        referenceMidFft(i, :) = abs(fft(referenceMidAnalyzedPartsTemp(j, (double(fftSize) * (i - 1) + 1) : (double(fftSize) * i) )));
                    end
                    if size(referenceMidFft, 1) == 1
                        referenceMidAverageFft(j, :) = referenceMidFft;
                    else
                        referenceMidAverageFft(j, :) = sum(referenceMidFft) ./ referenceMidFftCount;
                    end
                    clearvars referenceMidFft;
                end
                
                disp('Calculating average FFT of target mid...')
                if size(targetMidAverageFft, 1) == 1
                    targetMidCompletedFft = targetMidAverageFft;
                else
                    targetMidCompletedFft = sum(targetMidAverageFft) ./ size(targetMidAnalyzedParts, 1);
                end
                disp('Calculating average FFT of reference mid...')
                if size(referenceMidAverageFft, 1) == 1
                    referenceMidCompletedFft = referenceMidAverageFft;
                else
                    referenceMidCompletedFft = sum(referenceMidAverageFft) ./ size(referenceMidAnalyzedPartsTemp, 1);
                end
                
                disp('Calculating mid matching FFT...')
                targetMidCompletedFft(targetMidCompletedFft < 0.000001) = 0.000001;
                midMatchingFft = referenceMidCompletedFft ./ targetMidCompletedFft;
                
                disp('Partly cleaning memory...')
                clearvars referenceMidFft* targetMidFft*;
                
                disp('Filtering mid matching FFT...')
                gridLinear = targetSamplingFrequency / 2 * linspace(0, 1, double(fftSize) / 2 + 1);
                gridLogarithmic = targetSamplingFrequency / 2 * logspace(log10(4 / double(fftSize)), 0, (double(fftSize) / 2) * double(linLogOversampling) + 1); % Oversampling here
                midMatchingFftLogarithmic = interp1(gridLinear, midMatchingFft(1 : double(fftSize) / 2 + 1), gridLogarithmic, 'spline');
                
                midMatchingFftLogarithmicFiltered = smooth(midMatchingFftLogarithmic, 0.075,'loess')';
                midMatchingFftFiltered = interp1(gridLogarithmic, midMatchingFftLogarithmicFiltered, gridLinear,'spline');
                
                midMatchingFftFiltered(double(fftSize) / 2 + 2 : double(fftSize)) = midMatchingFftFiltered(double(fftSize) / 2 : -1 : 2);
                midMatchingFftFiltered(1) = 0; % Remove DC offset, lol
                midMatchingFftFiltered(2) = midMatchingFft(2);
                midMatchingFftFiltered(double(fftSize)) = midMatchingFft(double(fftSize));
                
                disp('Calculating mid FIR for matching EQ...')
                midFirTmp = real(ifft(midMatchingFftFiltered));
                midFir = ifftshift(midFirTmp);
                midFirHann = midFir .* hann(double(fftSize))';
                clearvars midFirTmp midFir;
                
                % ---SIDE---
                
                disp(['Calculating ', num2str(targetSideFftCount * size(targetSideAnalyzedParts, 1)), ' FFTs of target side...'])
                targetSideAverageFft = zeros(size(targetSideAnalyzedParts, 1), double(fftSize));
                for j = 1 : 1 : size(targetSideAnalyzedParts, 1)
                    targetSideFft = zeros(targetSideFftCount, double(fftSize));
                    for i = 1 : 1 : targetSideFftCount
                        targetSideFft(i, :) = abs(fft(targetSideAnalyzedParts(j, (double(fftSize) * (i - 1) + 1) : (double(fftSize) * i) )));
                    end
                    if size(targetSideFft, 1) == 1
                        targetSideAverageFft(j, :) = targetSideFft;
                    else
                        targetSideAverageFft(j, :) = sum(targetSideFft) ./ targetSideFftCount;
                    end
                    clearvars targetSideFft;
                end
                
                disp(['Calculating ', num2str(referenceSideFftCount * size(referenceSideAnalyzedPartsTemp, 1)), ' FFTs of reference side...'])
                referenceSideAverageFft = zeros(size(referenceSideAnalyzedPartsTemp, 1), double(fftSize));
                for j = 1 : 1 : size(referenceSideAnalyzedPartsTemp, 1)
                    referenceSideFft = zeros(referenceSideFftCount, double(fftSize));
                    for i = 1 : 1 : referenceSideFftCount
                        referenceSideFft(i, :) = abs(fft(referenceSideAnalyzedPartsTemp(j, (double(fftSize) * (i - 1) + 1) : (double(fftSize) * i) )));
                    end
                    if size(referenceSideFft, 1) == 1
                        referenceSideAverageFft(j, :) = referenceSideFft;
                    else
                        referenceSideAverageFft(j, :) = sum(referenceSideFft) ./ referenceSideFftCount;
                    end
                    clearvars referenceSideFft;
                end
                
                disp('Calculating average FFT of target side...')
                if size(targetSideAverageFft, 1) == 1
                    targetSideCompletedFft = targetSideAverageFft;
                else
                    targetSideCompletedFft = sum(targetSideAverageFft) ./ size(targetSideAnalyzedParts, 1);
                end
                disp('Calculating average FFT of reference side...')
                if size(referenceSideAverageFft, 1) == 1
                    referenceSideCompletedFft = referenceSideAverageFft;
                else
                    referenceSideCompletedFft = sum(referenceSideAverageFft) ./ size(referenceSideAnalyzedPartsTemp, 1);
                end
                
                disp('Calculating side matching FFT...')
                targetSideCompletedFft(targetSideCompletedFft < 0.000001) = 0.000001;
                sideMatchingFft = referenceSideCompletedFft ./ targetSideCompletedFft;
                
                disp('Partly cleaning memory...')
                clearvars referenceSideFft* targetSideFft*;
                
                disp('Filtering side matching FFT...')
                sideMatchingFftLogarithmic = interp1(gridLinear, sideMatchingFft(1 : double(fftSize) / 2 + 1), gridLogarithmic, 'spline');
                
                sideMatchingFftLogarithmicFiltered = smooth(sideMatchingFftLogarithmic, 0.075, 'loess')';
                sideMatchingFftFiltered = interp1(gridLogarithmic, sideMatchingFftLogarithmicFiltered, gridLinear, 'spline');
                
                sideMatchingFftFiltered(double(fftSize) / 2 + 2 : double(fftSize)) = sideMatchingFftFiltered(double(fftSize) / 2 : -1 : 2);
                sideMatchingFftFiltered(1) = 0; % Remove DC offset, lol
                sideMatchingFftFiltered(2) = sideMatchingFft(2);
                sideMatchingFftFiltered(double(fftSize)) = sideMatchingFft(double(fftSize));
                
                disp('Calculating side FIR for matching EQ...')
                sideFirTemp = real(ifft(sideMatchingFftFiltered));
                sideFir = ifftshift(sideFirTemp);
                sideFirHann = sideFir.*hann(double(fftSize))';
                clearvars sideFirTemp sideFir;
                
                disp('Convolving target with calculated FIRs...')
                tic;
                
                outputStage1MidTemp = outputStage1(:, 1)';
                outputStage2MidTemp = fconv(outputStage1MidTemp, midFirHann);
                outputStage1SideTemp = outputStage1(:, 2)';
                outputStage2SideTemp = fconv(outputStage1SideTemp, sideFirHann);                    
                disp(['Done convolution in ', num2str(toc), ' sec.'])
                disp('Cutting convolution edges and converting MS to LR...')
                outputStage2Mid = outputStage2MidTemp( (double(fftSize) / 2 + 1) : (size(outputStage2MidTemp, 2) - double(fftSize) / 2 + 1) )';
                outputStage2Side = outputStage2SideTemp( (double(fftSize) / 2 + 1) : (size(outputStage2SideTemp, 2) - double(fftSize) / 2 + 1) )';
                outputStage2(:, 1) = outputStage2Mid + outputStage2Side;
                outputStage2(:, 2) = outputStage2Mid - outputStage2Side;
                
                disp('Partly cleaning memory...')
                clearvars -except currentSessionStatus outputStage2 finalAmplitudeCoefficient pathWorkspace fileTarget fileReference pathTemp pathBin fileBrickwallLimiter maxLength timeArea fftSize linLogOversampling peakCompensationSteps targetSamplingFrequency targetDivisions targetPartSize referenceMatchingRms;
                
                disp('Stage 2 completed')
                
                disp('--------------------------------')
                
                % Stage 3 - RMS Correction
                
                disp('Stage 3 - RMS Correction')
                
                currentSessionStatus = 6;
                
                % Check to use limiter or not
                usingLimiter = true;
                if strcmp(pathBin, '') == true
                    usingLimiter = false;
                    disp('Brickwall limiter will not be used')
                end
                
                disp('Calculating temp mid channel of matched target...')
                outputStage2Mid(:) = (outputStage2(:, 1) + outputStage2(:, 2)) ./ 2;
                
                % Will process outputStage3 in next 'for'
                outputStage3 = outputStage2;
                
                for p = 1 : 1 : peakCompensationSteps
                    % Limiter emulation :)
                    if p < peakCompensationSteps
                        outputStage2MidLimited = outputStage2Mid;
                        disp(['Applying peak compensation #', num2str(p), ': simple algorithm...'])
                        outputStage2MidLimited( outputStage2MidLimited > 1 ) = 1;
                        outputStage2MidLimited( outputStage2MidLimited < -1 ) = -1;
                    end
                    
                    % Loading brickwall limiter
                    if p == peakCompensationSteps
                        if usingLimiter == false
                            break
                        end
                        disp(['Applying peak compensation #', num2str(p), ': complex algorithm...'])
                        audiowrite([pathTemp, 'tempnolim.wav'], outputStage2Mid, targetSamplingFrequency, 'BitsPerSample', 32);
                        command = ['"', pathBin, 'mrswatson64.exe" -p "', pathBin, fileBrickwallLimiter, '" -b 2048 -i "', pathTemp, 'tempnolim.wav" -o "', pathTemp, 'templim.wav"'];
                        [~, ~] = system(command);
                        [outputStage2MidLimited, ~] = audioread([pathTemp, 'templim.wav']);
                        delete([pathTemp, 'tempnolim.wav']);
                        delete([pathTemp, 'templim.wav']);
                    end
                    
                    % Some code from Stage 1
                    outputStage2Rmses = zeros(1, targetDivisions);
                    for i = 1 : 1 : targetDivisions
                        outputStage2Rmses(i) = rms(outputStage2MidLimited( (targetPartSize * (i - 1) + 1) : (targetPartSize * i) ));
                    end
                    
                    outputStage2AverageRms = rms(outputStage2Rmses);
                    
                    % May add array preallocation here in future
                    j = 1;
                    for i = 1 : 1 : targetDivisions
                        if outputStage2Rmses(i) >= (outputStage2AverageRms)
                            outputStage2AnalyzedPartNumbers(j) = i;
                            j = j + 1;
                        end
                    end
                    outputStage2AnalyzedRmses = zeros(1, size(outputStage2AnalyzedPartNumbers, 2));
                    for i = 1 : 1 : size(outputStage2AnalyzedPartNumbers, 2)
                        outputStage2AnalyzedRmses(i) = outputStage2Rmses(outputStage2AnalyzedPartNumbers(i));
                    end
                    
                    disp(['Current average RMS value in loudest parts is ', num2str(rms(outputStage2AnalyzedRmses))])
                    % ---
                    
                    outputStage2AnalyzedRmses(outputStage2AnalyzedRmses < 0.000001) = 0.000001;
                    rmsCoefficient = referenceMatchingRms / rms(outputStage2AnalyzedRmses);
                    
                    if p < peakCompensationSteps
                        disp(['The RMS correction coefficient #', num2str(p), ' is: ', num2str(rmsCoefficient), '. Modifying amplitudes...'])
                        outputStage2Mid = outputStage2Mid .* rmsCoefficient;
                        outputStage3 = outputStage3 .* rmsCoefficient;
                    end
                    
                    clearvars outputStage2AnalyzedPartNumbers outputStage2AnalyzedRmses outputStage2MidLimited;
                end
                
                disp(['The final RMS correction coefficient is: ', num2str(rmsCoefficient), '. Modifying amplitudes of the target...'])
                outputStage3 = outputStage3 .* rmsCoefficient;
                
                disp('Partly cleaning memory...')
                clearvars -except currentSessionStatus outputStage3 finalAmplitudeCoefficient usingLimiter pathWorkspace fileTarget fileReference pathTemp pathBin fileBrickwallLimiter maxLength timeArea fftSize linLogOversampling peakCompensationSteps targetSamplingFrequency;
                
                disp('Stage 3 completed')
                
                disp('--------------------------------')
                
                % Final Stage - Export
                
                disp('Final Stage - Export')
                
                currentSessionStatus = 7;
                
                if usingLimiter == true
                    % If using limiter, let's make 24-bit and 16-bit WAVs
                    
                    % We need to compensate first 1041 empty samples from brickwall limiter (this magic number is tested only on Voxengo Elephant)
                    outputSize = size(outputStage3, 1);
                    % delayCompensation is a number how much samples with 0 we need to add to the out to be like 2048*n+1
                    delayCompensation = 2048 * (fix(outputSize / 2048) + 1) - outputSize + 1;
                    disp(['Adding ', num2str(delayCompensation), ' zeroes in the end of modified target to make delay compensation...'])
                    outputStage3(outputSize + 1 : outputSize + delayCompensation, :) = 0;
                    
                    % Loading brickwall limiter for final limiting
                    disp('Limiting modified target...')
                    audiowrite([pathTemp, 'tempfinnolim.wav'], outputStage3, targetSamplingFrequency, 'BitsPerSample', 32);
                    command = ['"', pathBin, 'mrswatson64.exe" -p "', pathBin, fileBrickwallLimiter, '" -b 2048 -i "', pathTemp, 'tempfinnolim.wav" -o "', pathTemp, 'tempfinlim.wav"'];
                    [~, ~] = system(command);
                    [outputStage4, ~] = audioread([pathTemp, 'tempfinlim.wav']);
                    delete([pathTemp,'tempfinnolim.wav']);
                    delete([pathTemp,'tempfinlim.wav']);
                    
                    % Trimming
                    disp('Processing delay compensation...')
                    outputStage4 = outputStage4( (1041 + 1) : (1041 + size(outputStage4, 1) - 2048 - delayCompensation + 1), :);
                    %clearvars outputStage4;
                    
                    if finalAmplitudeCoefficient ~= 1
                        % Modifying with final coefficient
                        disp(['Modifying amplitudes with final aplitude coefficient: ', num2str(finalAmplitudeCoefficient), '...'])
                        outputStage4 = outputStage4 .* finalAmplitudeCoefficient;
                    end
                    
                    currentSessionStatus = 8;
                    
                    % Final saving to WAV 24-bit
                    fileOutput = ['[Matchered 24-bit] ', fileTarget];
                    disp(['Saving modified target audio in WAV 24bit to ', pathWorkspace, fileOutput, '...'])
                    audiowrite([pathWorkspace, fileOutput], outputStage4, targetSamplingFrequency, 'BitsPerSample', 24);
                    disp([fileOutput, ' saved'])
                    
                    % Final saving to WAV 16-bit
                    fileOutput = ['[Matchered 16-bit] ', fileTarget];
                    disp(['Saving modified target audio in WAV 16bit to ', pathWorkspace, fileOutput, '...'])
                    audiowrite([pathWorkspace, fileOutput], outputStage4, targetSamplingFrequency, 'BitsPerSample', 16);
                    disp([fileOutput, ' saved'])
                    
                    currentSessionStatus = 9;
                else
                    % If not using limiter, let's make just 32-bit WAV
                    
                    if finalAmplitudeCoefficient ~= 1
                        % Modifying with final coefficient
                        disp(['Modifying amplitudes with final aplitude coefficient: ', num2str(finalAmplitudeCoefficient), '...'])
                        outputStage4 = outputStage3 .* finalAmplitudeCoefficient;
                    else
                        outputStage4 = outputStage3;
                    end
                    
                    currentSessionStatus = 8;
                    
                    % Final saving to WAV 32-bit 
                    fileOutput = ['[Matchered 32-bit NO LIMITING] ', fileTarget];
                    disp(['Saving modified target audio in WAV 32bit to ', pathWorkspace, fileOutput, '...'])
                    audiowrite([pathWorkspace, fileOutput], outputStage4, targetSamplingFrequency, 'BitsPerSample', 32);
                    disp([fileOutput, ' saved'])
                    
                    currentSessionStatus = 9;
                end
                
                currentSessionStatus = 9;
                                
                disp('Final stage completed')
                
            end
        end
    end
end
    
% Cleaning for safe...
clearvars -except currentSessionStatus

disp('----------------------------------------------------------------')

disp('Stopping DSP Module...')

end