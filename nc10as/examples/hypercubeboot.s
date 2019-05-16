       MOVW 8192,R1        ;ID is memory location
                         ;containing the processor ID
;;; It was called IDREG in the example, but it should be PI (or #4)
       LDPR R1,#4   ;the ID is loaded into the ID
                         ;processor register
       FFOW R1,R2         ;R2 = # of trailing zeros in ID
       SUBB #1,R2      ;
       JMP END            ;no trailing zeros => this
                         ;processor is a leaf on the graph
LOOP:  MOVW #1,R3        ;compute ID of neighbor by
                         ;complementing one of the
       SFTW R2,R3        ;trailing zeros
       MOVW R1,R4        ;
       XORW R3,R4        ; R4 = new ID{send message length to port #(R2)}
                         ; {receive status; use timeout}
                         ;     a. dead (timed out)
                         ;     b. failed self test
                         ;     c. parity errord. alive and well
                         ; {if alive MOVW R4,ID;put new ID in memory}
                         ; {send copy of code and new ID to R2}
       REPNZ R2           ;
       JMP LOOP          ;
END:                     ;{look for responses and EROF}
