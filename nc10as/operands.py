#!/usr/bin/env python3

'''This is an operand parser and decoder for the ncube10 operand syntax.

See the 'parse_operand' and 'operand_disass' functions.

The idea is that we fully debug this "reference" version written in
python before translating it into much more brittle C in ncube10-opc.d
and ncube10-dis.c.

Notes:
 - The code is less "Pythonic" than it could be to facilitate
straightforward traslation.

 - Ncube's addressing mode syntax is close to, but not exactly the
same as PDP-11 syntax.

'''

import re
import struct

class Operand:
    def __init__(self, mnem, type=None):
        self.mnemonic = mnem
        self.encoded, self.desc = parse_operand(mnem, type)
        self.encoded_len = [len(self.encoded), len(self.encoded)] if self.encoded else [1, 5]

    repr_names = ('mnemonic', 'encoded', 'desc', 'encoded_len')
    def __repr__(self):
        return self.__class__.__name__ + "(" + ", ".join([repr(getattr(self, n)) for n in self.repr_names]) + ")"

    # we use the bounds on the encoded_len to resolve labels into
    # immediate operands.  The size of the insn depends on the
    # magnitude of the value stored in the immediate.
    #
    # FIXME - this whole encoded_len thing smells bad.  It's ugly and
    # it doesn't even work properly.
    def narrow_encoded_len(self, delta_min, delta_max):
        changed = False
        if delta_max < 32 and delta_max >= -32:
            lmax = 1
        elif delta_max < 128 and delta_max >= -128:
            lmax = 2
        elif delta_max < 32768 and delta_max >= -32768:
            lmax = 3
        else:
            lmax = 5
        if lmax != self.encoded_len[1]:
            changed = True
            self.encoded_len[1] = lmax

        if delta_min < 32 and delta_min >= -32:
            lmin = 1
        elif delta_min < 128 and delta_min >= -128:
            lmin = 2
        elif delta_min < 32768 and delta_min >= -32768:
            lmin = 3
        else:
            lmin = 5
        if lmin != self.encoded_len[0]:
            changed = True
            self.encoded_len[0] = lmin
            
        return changed
    
def report_err(s):
    raise RuntimeError(s)

def atoi(s):
    # In python we'll use int.  In C, use
    # atoi or sscanf(%i)
    return int(s)

def atof(s):
    # In python we'll use float.  In C, use
    # atof or sscanf(%f)
    return float(s)

def inrange(n, bits, signed):
    if signed:
        max = (1<<(bits-1)) - 1
        min =  -(1<<(bits-1))
    else:
        max = (1<<bits) - 1
        min = 0
    return n >= min and n <= max

def integer_range(i, signed):
    sign = '' if signed else 'u'
        
    if inrange(i, 8, signed):
        return sign + 'byte', 0
    elif inrange(i, 16, signed):
        return sign + 'halfword', 1
    elif inrange(i, 32, signed):
        return sign + 'word', 2
    else:
        report_err('integer out of range')
    
def valid_label(s):
    # Rather than write our own regex, just use python's rules:
    return s.isidentifier()

def encode(MD, Reg, Atype, A, msg):
    b = MD<<4 | (Reg&0x3f) # take care with sign-extending Reg...
    fmt = '<B'
    if Atype is None:
        return struct.pack(fmt, b), msg
    if Atype.endswith('byte'):
        fmt += 'b'
    elif Atype.endswith('halfword'):
        fmt += 'h'
    elif Atype.endswith('word'):
        fmt += 'i'
    elif Atype == 'real':
        fmt += 'f'
    elif Atype == 'longreal':
        fmt += 'd'
    if Atype.startswith('u'):
        fmt = fmt.upper()
    
    return struct.pack(fmt, b, A), msg

# NOTE:  the LDPR and STPR instructions (any others??) take
# a 'byte' argument to indicate *which* Processor Register
# we're talking about.  We allow them as special cases
# of parse_immediate, e.g., #PI is the  same as #4.
# The special cases are:
#  0 SP Stack Pointer
#  1 PS Program Status
#  2 FR Fault Register
#  3 CR Configuration Register
#  4 PI Processor ID
#  5 OR Output Ready (read only)
#  6 IR Input Ready (read only)
#  7 OE Output Enable
#  8 IE Input Enable
#  9 IP Input Pending (read only)
# 10 PE Parity Error (read only)
# 11 IO Input Overrun (read only)
named_immediates = {name:idx for idx,name in enumerate(('SP', 'PS', 'FR', 'CR', 'PI', 'OR', 'IR', 'OE', 'IE', 'IP', 'PE', 'IO'))}
# They're spelled differently in the asm listings in the patent:
named_immediates['CONFIG'] = named_immediates['CR']
named_immediates['IDREG'] = named_immediates['PI']
named_immediates['INPEND'] = named_immediates['IP']
named_immediates['INRDY'] = named_immediates['IR']
named_immediates['OUTRDY'] = named_immediates['OR']

def parse_immediate(s, type):
    if type == 'real' or type == 'longreal':
        f = atof(s)
        n = int(f)
        if f != n or not inrange(n, 6, True):
            return encode(0xF, 0xD, type, f, 'F D %s(%g) # immediate'%(type, f))
    elif s in named_immediates:
        n = named_immediates[s]
    else:
        n = atoi(s)
    if inrange(n, 6, True):
        return encode(0, n, None, None, '0 (6-bits)%d # literal'%n)
    else:
        # FIXME(?) - the only way to set the high bit is to give
        # a negative value.  I.e., we can't say 
        #    ORB #129,R13
        # Instead,  we have to say:
        #    ORB #-127,R13
        # Note that 4.3.1 says "most instructions treat integers as
        # signed numbers but the logical operations (e.g., AND, OR) view
        # their operands as unsigned quantities.  Addresses are also
        # treated by the processor as unsigned values".  OTOH, it also
        # says that "The ranges for the three integer formats are
        # specified as follows:  
        #   Byte (B): -128 to 127
        #   Halfword(H):  -32768, 32767
        #   Word(W): -2147483648, 2147483647
        # It's not unreasonable to say that immediates should stay
        # in-range.
        type,_ = integer_range(n, signed=True)
        return encode(0xF, 0xD, type, n, 'F D %s(%d)# immediate'%(type, n))

def parse_register_number(register):
    Rn = atoi(register)
    if Rn > 15:
        report_err('Rn outside range 0-15')
    return Rn

# FIXME - we need to allow labels as operands.  The ATT syntax appears
# to be an 'identifier' starts with a letter.  There are also local
# lables that start with a dot.  Do we worry about disambiguating a
# label called, e.g., R3 or SP from a named register?   What should
# parse_operand return when the arg is a label?  When an operand
# is a label, can it be turned into anything *but* a A(PC) operand?
# How is this handled by gas and binutils??  How much is in the
# arch-specific-op.c and how much is in generic code??

rx = re.compile(r"""(@)?        # m[1]: optional @
                  ([-0-9x]*)  # m[2]: Offset/Index or autodecrement
                  (\((R[0-9]{1,2}|PC|SP)\))? # m[4]: Rn|PC|SP
                  (\+{,2})""",  # m[5]: autoincrement
                re.VERBOSE)


# This is main reference/debug entry point for testing the
# assembly direction (mnemonic -> object)
def parse_operand(s, type=None):
    # Arguments: s is the operand, e.g., '@88(R15)' (it is assumed to
    # be 'strip'ed).  type is the expected type of the operand.
    # 
    # Returns: a tuple: (bytestring, 'descriptive text') The
    # bytestring is memory representation that would follow the opcode
    # in memory.  The descriptive text refers to the type of operand
    # that we think we converted.  Use it for debugging.  It uses the
    # same terminology as the Addressing Mode Table in the
    # documentation.  If the operand is a label, then descriptive text
    # is the string 'label' and the bytestring is None. 
    #
    # The caller is parse_operand calls report_err (which throws a
    # RuntimeError) if it can't parse the operand.
    if s[0] == '#':
        return parse_immediate(s[1:], type)
    if s[0] == 'S':
        if s == 'STK':  # N.B.  should be SP?  See the detailed
            # description of PUSH POP operands in the docs.
            return encode(0xF, 0xC, None, None, 'F C # Push/Pop')
    if s[0] == 'R':
        try:
            Rn = parse_register_number(s[1:])
            return encode(0xC, Rn, None, None, 'C %X # register direct'%(Rn))
        except:
            # it might be a label, e.g., RETRY:
            pass 
    
    m = rx.fullmatch(s)
    if not m:
        if type is 'address' and valid_label(s):
            return (None, 'label')
        else:
            report_err('Unparseable operand')
        
    at_indirect = bool(m[1])
    A = m[2]

    autodec = (A == '-')
    if autodec:
        A = None
    register = m[4]
    autoinc = m[5]
    autoskip = (autoinc == '++')

    if register and register[0] == 'R':
        Rn = parse_register_number(register[1:])
    else:
        Rn = None

    if not A:
        if autoinc and autodec:
            report_err('Autoincrement and autodecrement cannot both be present')
        if Rn is None:
            report_err('Register indirect requires a general purpose register')
        if (autodec or autoskip) and at_indirect:
            report_err('Autodecrement/autoskip and @indirect cannot both be present')
        if at_indirect and not autoinc:
            report_err('@A(Rn) requires non-empty A or autoincrement')
        if autoskip:
            return encode(0x5, Rn, None, None, '5 %d # Autoskip'%Rn)
        if autoinc:
            if at_indirect:
                return encode(0x7, Rn, None, None, '7 %d # Autoincrement indirect'%Rn)
            else:
                return encode(0x6, Rn, None, None, '6 %d # Autoincrement'%Rn)
        if autodec:
            return encode(0xD, Rn, None, None, 'D %d # Autodecrement'%Rn)
        return encode(0x4, Rn, None, None, '4 %d # Register indirect'%Rn)
        
    # We've definitely got an A index/offset
    # register is either 'PC' or 'SP' or None
    if autoinc or autodec:
        report_err('Auto(inc|dec)rement not with index/offset')

    try:
        iA = atoi(A)
    except ValueError:
        report_err('Offset not parseable as integer')

    # Direct addresses, e.g., A, @A, are unsigned
    Asigned = register is not None

    # N.B.  widthbits is *not* the width of A.  It's the bits
    # that we 'or' into one of the nibbles of the mode specifier to
    # designate whether A is a byte, halfword, word or address.
    Atype,widthbits = integer_range(iA, Asigned)
    
    if at_indirect:
        Atype = 'word'
        widthbits = 3
                 
    arg = Atype + '(%d)'%iA
        
    if Rn is not None:
        return encode(8+widthbits, Rn, Atype, iA, '%X %X %s # Offset+Register Indirect'%(8+widthbits, Rn, arg))

    
    # We're now done with modes that have a general register.
    # All that's left are 'Special' modes from the second part
    # of the table.  All these modes are encoded with a
    # 'Mode specifier' of F.  
    
    if register is None:
        regbit = 8
    elif register == 'SP':
        regbit = 4
    elif register == 'PC':
        regbit = 0
    else:
        report_err('Expected SP or PC relative addressing')

    return encode(0xF, regbit+widthbits, Atype, iA, 'F %X %s # special modes no general register'%(regbit + widthbits, arg))
        
def decode_immediate(bstr, type):
    if type == 'byte':
        return '#%d'%(struct.unpack('b', bstr))
    elif type == 'halfword':
        return '#%d'%(struct.unpack('h', bstr))
    elif type == 'word':
        return '#%d'%(struct.unpack('i', bstr))
    elif type == 'real':
        return '#%.9g'%(struct.unpack('f', bstr))
    elif type == 'longreal':
        return '#%.17g'%(struct.unpack('d', bstr))
    else:
        report_err('decode_immediate')

# This is main reference/debug entry point for testing the
# disassembly direction (object -> mnemonic).  The 'isfloat
# argument is necessary only to disambiguate whether a
# four-bytes #immedate should be interpreted as a float
# or an integer.
def operand_disass(hexstr, isfloat=None):
    b = bytes.fromhex(hexstr)
    b0 = struct.unpack('B', b[:1])[0]
    MD = b0>>4
    REG = b0 & 0xf;
    if MD <= 3:
        n = (MD<<4) | REG
        # sign-extend:
        if n >= 32:
            n -= 64
        return '#%d'%n
    elif MD == 4:
        return '(R%d)'%REG
    elif MD == 5:
        return '(R%d)++'%REG
    elif MD == 6:
        return '(R%d)+'%REG
    elif MD == 7:
        return '@(R%d)+'%REG
    elif MD == 0xC:
        return 'R%d'%REG
    elif MD == 0xD:
        return '-(R%d)'%REG
    elif MD == 0xE:
        return 'RES'
    # Everything below here has a following 'A' value
    elif MD == 0xF:
        if REG == 0xC:
            return 'STK'
        elif REG == 0xD:
            if len(b) == 2:
                type = 'byte'
            elif len(b)== 3:
                type = 'halfword'
            elif len(b) == 9:
                type = 'longreal'
            elif len(b) == 5:
                if isfloat is None:
                    report_err('Cannot distinguish between float and word immediates.  Try again with either type="real" or type="word"')
                type = 'real' if isfloat else 'word'
            return decode_immediate(b[1:], type)
        elif REG == 0xE:
            return 'RES'
        elif REG == 0xF:
            return 'ESC'
        else:
            widthbits = REG&0x3
            if REG < 0x4:
                regname = '(PC)'
            elif REG < 0x8:
                regname  = '(SP)'
            else:
                regname = ''
    else:
        # MD = 8, 9, A, or B
        regname = '(R%d)'%REG
        widthbits = MD&0x3
    at_indirect = '@' if widthbits == 3 else ''
    if widthbits == 0:
        fmt = 'b'
    elif widthbits == 1:
        fmt = 'h'
    else:
        fmt = 'i'

    if regname  == '':
        fmt = fmt.upper()
    
    iA = struct.unpack('<' + fmt, b[1:])[0]
    return at_indirect + '%d'%iA + regname
    
    
def roundtrip(s, type = None):
    hexstr = parse_operand(s, type)
    isfloat = type == 'real'
    print("object code: ", hexstr)
    ss = operand_disass(hexstr[0], isfloat)
    print("disassembled: ", ss)
    h2 = parse_operand(ss, type)
    assert h2 == hexstr
    ss2 = operand_disass(h2[0], isfloat)
    assert ss2 == ss
    
