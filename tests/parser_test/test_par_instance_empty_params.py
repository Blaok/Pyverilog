from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.parser.parser import VerilogCodeParser

try:
    from StringIO import StringIO
except:
    from io import StringIO

codedir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
Source:  (at 1)
  Description:  (at 1)
    Module: TOP, None (at 1)
      DeclVars:  (at 3)
        Var:  (at 3)
          Input: CLK, None (at 3)
      DeclVars:  (at 4)
        Var:  (at 4)
          Input: RST, None (at 4)
      DeclVars:  (at 5)
        Var:  (at 5)
          Output: LED, None (at 5)
            Width:  (at 5)
              IntConst: 7 (at 5)
              IntConst: 0 (at 5)
      DeclInstances:  (at 9)
        Instance: led, inst_led (at 9)
          PortArg: CLK (at 14)
            Identifier: CLK (at 14)
          PortArg: RST (at 15)
            Identifier: RST (at 15)
          PortArg: LED (at 16)
            Identifier: LED (at 16)
    Module: led, None (at 21)
      DeclParameters:  (at 23)
        Parameter: STEP, None, None (at 23)
          Rvalue:  (at 23)
            IntConst: 10 (at 23)
      DeclVars:  (at 26)
        Var:  (at 26)
          Input: CLK, None (at 26)
      DeclVars:  (at 27)
        Var:  (at 27)
          Input: RST, None (at 27)
      DeclVars:  (at 28)
        Var:  (at 28)
          Output: LED, None (at 28)
            Width:  (at 28)
              IntConst: 7 (at 28)
              IntConst: 0 (at 28)
          Reg: LED, None (at 28)
            Width:  (at 28)
              IntConst: 7 (at 28)
              IntConst: 0 (at 28)
      DeclVars:  (at 31)
        Var:  (at 31)
          Reg: count, None (at 31)
            Width:  (at 31)
              IntConst: 31 (at 31)
              IntConst: 0 (at 31)
      Always:  (at 33)
        SensList:  (at 33)
          Sens: posedge (at 33)
            Identifier: CLK (at 33)
        Block: None (at 33)
          IfStatement:  (at 34)
            Identifier: RST (at 34)
            Block: None (at 34)
              NonblockingSubstitution:  (at 35)
                Lvalue:  (at 35)
                  Identifier: count (at 35)
                Rvalue:  (at 35)
                  IntConst: 0 (at 35)
              NonblockingSubstitution:  (at 36)
                Lvalue:  (at 36)
                  Identifier: LED (at 36)
                Rvalue:  (at 36)
                  IntConst: 0 (at 36)
            Block: None (at 37)
              IfStatement:  (at 38)
                Eq:  (at 38)
                  Identifier: count (at 38)
                  Minus:  (at 38)
                    Identifier: STEP (at 38)
                    IntConst: 1 (at 38)
                Block: None (at 38)
                  NonblockingSubstitution:  (at 39)
                    Lvalue:  (at 39)
                      Identifier: count (at 39)
                    Rvalue:  (at 39)
                      IntConst: 0 (at 39)
                  NonblockingSubstitution:  (at 40)
                    Lvalue:  (at 40)
                      Identifier: LED (at 40)
                    Rvalue:  (at 40)
                      Plus:  (at 40)
                        Identifier: LED (at 40)
                        IntConst: 1 (at 40)
                Block: None (at 41)
                  NonblockingSubstitution:  (at 42)
                    Lvalue:  (at 42)
                      Identifier: count (at 42)
                    Rvalue:  (at 42)
                      Plus:  (at 42)
                        Identifier: count (at 42)
                        IntConst: 1 (at 42)
"""


def test():
    filelist = [codedir + 'instance_empty_params.v']
    output = 'preprocess.out'
    include = [codedir]
    define = []

    parser = VerilogCodeParser(filelist,
                               preprocess_include=include,
                               preprocess_define=define)
    ast = parser.parse()
    directives = parser.get_directives()

    output = StringIO()
    ast.show(buf=output)

    for lineno, directive in directives:
        output.write('Line %d : %s' % (lineno, directive))

    rslt = output.getvalue()

    print(rslt)
    assert(expected == rslt)


if __name__ == '__main__':
    test()
