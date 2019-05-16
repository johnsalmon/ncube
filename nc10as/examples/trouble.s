;;; This is the screw-case for our inadequate approach to
;;; resolving labels.  The first JMP ZERO and JMP THIRTYTWO
;;; might be #-32 and #31 or #-33 and #32.  But our algorithm
;;; can't commit to one or the other.
ZERO:
	JMP THIRTYTWO
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP

	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP

	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP
	NOP

	NOP
	NOP
	NOP
	NOP
	NOP
THIRTYTWO:	
	NOP
	JMP ZERO

	
