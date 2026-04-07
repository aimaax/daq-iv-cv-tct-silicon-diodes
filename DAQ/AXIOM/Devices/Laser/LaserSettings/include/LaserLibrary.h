#pragma once

#if defined(LASERLIBRARY_EXPORTS) // inside DLL
#   define LIB_API_EXPORT   __declspec(dllexport)
#else // outside DLL
#   define LIB_API_EXPORT   __declspec(dllimport)
#endif  // XYZLIBRARY_EXPORT

/* This is method that check USB connection. */
extern "C" LIB_API_EXPORT bool checkDevice(void);

/* This is method that check the LASER state. */
extern "C" LIB_API_EXPORT bool checkLaserState(void);

/* This method sets the frequency of the laser. */
extern "C" LIB_API_EXPORT int setLaserFrequency(int frequency);

/* This method is used to turn off LASER. */
extern "C" LIB_API_EXPORT int turnLaserOff(void);

/* This method is used to toggle hardware sequence for ARM.  
	state = TRUE to turn on 
	state = FALSE to turn off
*/
extern "C" LIB_API_EXPORT int toggleHardSeq(bool state);

/* This method toggles DAC on ARM MCU. 
	state = TRUE to turn on DAC. Value set on DAC output will be 0x000 or last set data before disable command.
	state = FALSE to turn off DAC. Value set on DAC output will be 0x000.
*/
extern "C" LIB_API_EXPORT int toggleDAC(bool state);

/* ***NOT YET IMPLEMENTED BY PARTICULARS***
	This method toggles external interrupts on ARM MCU.
	state = TRUE to turn on
	state = FALSE to turn off
*/
extern "C" LIB_API_EXPORT int toggleEXTInterrupt(bool state);

/* This method toggles RIT.
	state = TRUE to turn on
	state = FALSE to turn off
*/
extern "C" LIB_API_EXPORT int toggleRIT(bool state);

/* This method is used to clean sequence data for ARM. */
extern "C" LIB_API_EXPORT int clearLaserMCU(void);

/* This method sets the value for DAC. Value is int which will be set on DAC output. */
extern "C" LIB_API_EXPORT int setLaserDAC(int value);

/* This is method is for sending data for RIT COMPARE value. */
extern "C" LIB_API_EXPORT int laserInterruptPeriod(long int value);

/* This is method that shows ADC data. */
extern "C" LIB_API_EXPORT double laserADCData(int channel);

/* This method is used to generate sequence. 
	*** No documentation on function however assuming: ***
	mode = 2 to load sequence
	mode = 1 to start sequence
	mode = 0 to clear sequence
*/
extern "C" LIB_API_EXPORT int laserSeqMode(int mode);

/* This method is used to send freq data to ARM. 
	*** Assuming use of function: Below is example used in PaLaser example to set pulse duration ***
	(!strcmp(argv[2],"pulse"))     {HIDDLL::sendFreq( (atoi(argv[3])-440)/180  ); printf("Pulse duration set\n");}
*/
extern "C" LIB_API_EXPORT int sendLaserFrequency(int frequency);

/* This is the method used for the activation of ADC. It returns value measured by ADC in ARM MCU. */
extern "C" LIB_API_EXPORT int acquireLaserADC(void);

/* This method is used to generate sequence. */
extern "C" LIB_API_EXPORT int generateSeq(void);

/* This function selects the default output file: streamFile.txt */
extern "C" LIB_API_EXPORT int defaultFile(void);

/* This method is used for selecting, parsing and sending data to ARM MCU from selected file. It opens select file dialog where file can be selected. 
	File should be formated properly. Below the function are the markers: 
*/
extern "C" LIB_API_EXPORT int selectOutputFile(char* dFile);

/*

		freq: 2											// marker for freq parameter followed by freq value

		seqLength: 344									// marker for length of the sequence parameter followed by seqLength value

		CH number: 4									// marker for selection of number for output channels. marker is followed by CH number value

		CH1:											// marker for channel data
		byte_0  byte_1 .................. byte_15 ;		// chanell data
		byte_16  ........................ byte_31 ;		// chanell data
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		byte_120 .......................  byte_127 ;	// chanell data

		CH2:											// marker for channel data
		byte_0  byte_1 .................. byte_15 ;		// chanel2 data
		byte_16  ........................ byte_31 ;		// chanel2 data
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		byte_120 .......................  byte_127 ;	// chanel2 data

		.                                  .
		.                                  .
		.                                  .
		.                                  .
		.                                  .
		.                                  .
		.                                  .

		CH8:											// marker for channel data
		byte_0  byte_1 .................. byte_15 ;		// chanel8 data
		byte_16  ........................ byte_31 ;		// chanel8 data
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		  .                                .	                .
		byte_120 .......................  byte_127 ;	// chanel8 data

		*/