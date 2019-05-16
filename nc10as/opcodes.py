#!/usr/bin/env python3

_tbl1 = """
  MOVB MOVH MOVW RES MOVR MOVL RES RES
  NEGB NEGH NEGW RES NEGR NEGL RES REP
  SBRB SBRH SBRW RES SBRR SBRL RES REPZ
  CMPB CMPH CMPW RES CMPR CMPL RES REPNZ
  ADDB ADDH ADDW RES ADDR ADDL RES TRAP
  ADCB ADCH ADCW RES SQTR SQTL RES RES
  SUBB SUBH SUBW RES SUBR SUBL RES RES
  SBBB SBBH SBBW RES SGNR SGNL RES RES
  MULB MULH MULW RES MULR MULL RES RES
  DVRB DVRH DVRW RES DVRR DVRL RES RES
  REMB REMH REMW RES REMR REML RES RES
  DIVB DIVH DIVW RES DIVR DIVL RES RES
  BITB BITH BITW RES RES  RES  RES RES
  RES  RES  RES  RES RES  RES  RES RES
  RES  RES  RES  RES RES  RES  RES RES
  RES  RES  RES  RES ESC  ESC  ESC RES
"""

_tbl2="""
 SFTB SFTH SFTW RES CVBR NOP  RES BG
 SFAB SFAH SFAW RES CVHR CLC  RES BLE
 ROTB ROTH ROTW RES CVWR STC  RES BGU
 FFOB FFOH FFOW RES CVLR CMC  RES BLEU
 ANDB ANDH ANDW RES CVBL ERON RES BGE
 ORB  ORH  ORW  RES CVHL EROF RES BL
 XORB XORH XORW RES CVWL BKPT RES BGEU
 NOTB NOTH NOTW RES CVRL RSET RES BLU
 ADCD RES  LDPR RES CVBW EI   RES BNE
 SBBD RES  STPR RES CVHW DI   RES BE
 RES  RES  LCNT RES CVWB RES  RES BNV
 RES  RES  LPTR RES CVWH RES  RES BV
 RES  RES  BCNT RES CVRW RETI RES CALL
 RES  RES  BPTR RES CVLW WAIT RES JMP
 RES  RES  MOVA RES RES  RET  RES RETP
 ESC  ESC  ESC  ESC ESC  ESC  ESC ESC
"""

_v1 = _tbl1.split()
_v2 = _tbl2.split()
_op2str = [None]*256
_str2op = {}
for i in range(128):
    _str2op[_v1[i]] = 2*i
    _str2op[_v2[i]] = 2*i+1
    _op2str[2*i] = _v1[i]
    _op2str[2*i+1] = _v2[i]

_typename = {'B': 'byte', 'H': 'halfword', 'W': 'word', 'R': 'real', 'L': 'longreal'}

def operand_types(op):
    TP = op & 0xf
    OP = (op>>4) & 0xf
    if TP==0 or TP==1:
        return ('byte',)*2
    elif TP==2 or TP==3:
        return ('halfword',)*2
    elif TP==4 or (TP==5 and OP<8):
        return ('word',)*2
    elif TP==5:
        # contrary to the table in 4.7.1, the
        # operands aren't necessarily a 'word'
        if OP==8: # LDPR
            return ('word', 'byte')
        elif OP==9: # STPR
            return ('byte', 'word')
        elif OP==10: # LCNT
            return ('word', 'byte')
        elif OP==11: # LPTR
            return ('word',  'word')
        elif OP==12: # BCNT
            return ('word', 'word')
        elif OP==13: # BPTR
            return ('word', 'word')
        elif OP==14: # MOVA
            return ('word', 'word') # ????
        else: #  OP==15: # ESC
            raise ValueError('operand_types(ESC opcode)')
    elif TP==6 or TP==7 or TP==12 or TP==13:
        raise ValueError('operand_types(REServed opcode)')
    elif TP==8:
        return ('real',)
    elif TP == 9:
        mnemonic = _op2str(op)
        From = mnemonic[-2]
        To = mnemonic[-1]
        return (_typename[From], _typename[To])
    elif TP==10:
        return ('longreal',)*2
    elif TP==11:
        return ()
    elif TP==14:
        if OP == 4:          # TRAP - "the source operand is an unsigned byte"
            return ('byte',) # unsigned
        elif OP==1 or OP==2 or OP==3: # REP[N[Z]] - "src must be a general register destination"
            return ('register',)
        else:
            raise ValueError('operand_types(REServed opcode)')
    elif TP==15:
        return ('address',)
        
