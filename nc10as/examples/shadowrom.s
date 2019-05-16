! During shadow ROM execution all interrupts are disabled including
! interrupts that are not normally maskable;
RSET ;

! The RAM chips need 8 refresh cycles to initialize themselves. The
! refresh rate starts at one refresh every 8 cycles since the Configuration
! register is set to zero on reset. We idle for the required 64 cycles by
! looping on RSET 10 times. Each loop takes 7 cycles (3 for the RSET and
! 4 for the REP);

MOVW #11,R0;
REP R0;
RSET;

! The refresh rate is lowered to every 40 cycles by writing a 4 in the
! Configuration register. This is conservatively high but the operating
! system can lower it further if the processor clock rate justifies it;

LDPR #4,#CONFIG

! Memory is now initialized with correct ECC bits by writing zero to
! every location. Since the Configuration register is initialized to
! assume 16k×4 memories, only the first quarter of memory is initialized
! by writing 8191 words. If the operating system changes the Configuration
! to 64k×4, then it should initialize the last 3/4 of memory;

MOVW #8191,R0;
MOVW #0,R1;
REP R0;
MOVW #0,(R1)+

! A self test belongs here. The result is encoded and stored in memory
! at location 4. A -1 means everything is fine;

MOVH #-1,4;

! Bit 31 of the ID Register is initialized when the reset pin is asserted
! with a one if the processor is an I/O processor or a zero is the processor
! is an array processor. I/O processors are initialized from memory while
! array processors are initialized by the serial ports;

STPR #IDREG,R0;
BL IOINIT

! Array processor initialization waits for a port to receive a
! message. The code below assumes that only one port will try to initialize
! the processor. If messages come in at two ports exactly at the same time,
! the code may not work;

PROCINIT: STPR #INPEND, R0  ! Are any incoming messages pending?
          BE PROCINIT       ! No, try again
          FFOW R0, R1       ! Yes, R1 gets the port number

! Initialize the port so DMA transfer of a two byte message to location
! 2 will occur;

LPTR #2,R1;
LCNT #2,R1;

! Compute in R3 the corresponding output port for a reply;

MOVW R1,R3;
ADDW #32,R3;

! Wait for incoming message DMA to complete;

INWAIT1: STPR #INRDY, R2   ! Store input ready flags in R2
         BITW R2, R0       ! Test the appropriate flag
         BE INWAIT1        ! Loop until port is ready

! Start the output port DMA. The message will be the two byte self test
! status in location 4;

LPTR #4,R3;
LCNT #2,R3;

! Reinitialize the same input port to receive the contents of memory;

         LPTR #8, R1      ! The message will start at location 8
         LCNT 2, R1       ! for number of bytes indicate by the first message

INWAIT2: STPR #6, R2  ! Wait for input DMA to complete by  #INRDY aka IR is #6
         BITW R2, R0      ! testing the appropriate ready flag
         BE INWAIT2       ! and looping back until ready (done)

! Jump to a preset location (1024) to begin execution from memory. The
! JMP resets the "shadow ROM active" flag;

JMP 1024;

! I/O processor initialization. Wait for memory location 0 or 1 to go
! nonzero. The external processor that loads the memory image must wait
! at least xxx cycles after the RESET signal has gone away;

IOINIT: BITH #-1,0   ! Test halfword at location 0
        BE IOINIT     ! Loop back until it becomes non-zero

! Jump to a preset location (1024) to begin execution from memory. The
! JMP resets the "shadow ROM active: flag;

JMP 1024;

! End of shadow Rom code;
