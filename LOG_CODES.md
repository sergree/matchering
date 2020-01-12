# Matchering 2.0 Log Codes Overview

Each **[Matchering 2.0](https://github.com/sergree/matchering)** processing error message begins with a special four-digit code. 

Also, if you call `mg.log(handler, show_codes=True)`, the default **info** and **warning** messages will also start displaying these codes.

This is done for the convenience of connecting this module to various backends. If the remote system knows the meaning of these codes, it can correctly respond to them, regardless of the platform.

### Info Codes

**Code**|**Meaning**
-----|-----
2001|Uploading files
2002|Queued for processing
2003|Loading and analysis
2004|Matching levels
2005|Matching frequencies
2006|Correcting levels
2007|Final processing and saving
2008|Exporting various audio formats
2009|Making previews
2010|The task is completed
2101|The TARGET audio is mono. Converting it to stereo...
2201|The REFERENCE audio is mono. Converting it to stereo...
2202|The REFERENCE audio was resampled
2203|Presumably the REFERENCE audio format is lossy

### Warning Codes

**Code**|**Meaning**
-----|-----
3001|Audio clipping is detected in the TARGET file. It is highly recommended to use the non-clipping version
3002|The applied limiter is detected in the TARGET file. It is highly recommended to use the version without a limiter
3003|The TARGET audio sample rate and internal sample rate were different. The TARGET audio was resampled
3004|Presumably the TARGET audio format is lossy. It is highly recommended to use lossless audio formats (WAV, FLAC, AIFF)

### Error Codes

**Code**|**Meaning**
-----|-----
4001|Audio stream error in the TARGET file
4002|Track length is exceeded in the TARGET file
4003|The track length is too small in the TARGET file
4004|The number of channels exceeded in the TARGET file
4005|The TARGET and REFERENCE files are the same. They must be different so that Matchering makes sense
4101|Audio stream error in the REFERENCE file
4102|Track length is exceeded in the REFERENCE file
4103|The track length is too small in the REFERENCE file
4104|The number of channels exceeded in the REFERENCE file
4201|Unknown error
4202|Validation failed! Please let the developers know about this error!
