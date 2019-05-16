;;; Loop over memory, writing zeros to bytes 32k-64k.
;;; Avoid fancy addressing modes and REP instructions.
RESTART:	
	MOVW #32768,R1;
LOOP:
	MOVW #0,(R1)
	ADDW #4, R1
	CMPW R1, #65536
	BL LOOP
	JMP RESTART
