;;; Minimal(!) program to see if we even know how to talk
;;; to the Ncube's serial port.
;;;
;;; The main hurdle is getting this code loaded and running.  Once
;;; it's running, it should write two bytes with value 'n' (110) and
;;; 'c' (99) to the host port

;;; The HOST port is #31 in OUTRDY, but it's 63 for LPTR and LCNT.
ORDY:
	STPR #OUTRDY, R0
	BGE ORDY 		; test bit 31 with BGE
;;; Store two bytes in memory at address 8192
	MOVB #110, 8192		; 'n'
	MOVB #99, 8193		; 'c'
;;; Send two bytes starting at address 8192
	LPTR 8192, #63
	LCNT #2, #63
	
;;; We're done.  Wait for an interrupt (which we're not expecting to ever come)
SPIN:	
	WAIT 			;
	JMP SPIN
