;;; Loop over memory, writing zeros to bytes 32k-64k.
;;; Use the REP instruction and the same idiom used in
;;; the shadow rom.
LOOP:	
	MOVW #8191,R0;
	MOVW #32768,R1;
	REP R0;
	MOVW #0,(R1)+
	JMP LOOP 		; keep going
