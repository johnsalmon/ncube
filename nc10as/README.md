## A rudimentary assembler for the Ncube10 instruction set

Usage:

```
   nc10as [--raw] filename ...
```

With --raw, the output is a single hex-encoded line of text.  E.g.,

```
bash-3.2$ ./nc10as memloop0.s --raw
04fdff1fc004fd0a800000c11ec0040061df2f
```

Without --raw, the output is much easier to read and debug.  It's also pretty
easy to turn into hex, e.g., with awk '{printf %s $2}'.

```
bash-3.2$ ./nc10as memloop0.s
0000: 04fdff1fc0             ; ['MOVW', '#8191', 'R0']
0005: 04fd0a800000c1         ; ['MOVW', '#32778', 'R1']
0012: 1ec0                   ; ['REP', 'R0']
0014: 040061                 ; ['MOVW', '#0', '(R1)+']
0017: df2f                   ; ['JMP', 'LOOP']
```

Some short programs are in examples/.
