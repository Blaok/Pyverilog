"""
   Copyright 2013, Shinya Takamaeda-Yamazaki and Contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import re


class Node(object):
    """ Abstact class for every element in parser """

    def children(self):
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, showlineno=True):
        indent = 2
        lead = ' ' * offset

        buf.write(lead + self.__class__.__name__ + ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % (n, v) for (n, v) in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showlineno:
            buf.write(' (at %s)' % self.lineno)

        buf.write('\n')

        for c in self.children():
            c.show(buf, offset + indent, attrnames, showlineno)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        self_attrs = tuple([getattr(self, a) for a in self.attr_names])
        other_attrs = tuple([getattr(other, a) for a in other.attr_names])

        if self_attrs != other_attrs:
            return False

        other_children = other.children()

        for i, c in enumerate(self.children()):
            if c != other_children[i]:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        s = hash(tuple([getattr(self, a) for a in self.attr_names]))
        c = hash(self.children())
        return hash((s, c))


# ------------------------------------------------------------------------------
class Source(Node):
    attr_names = ('name',)

    def __init__(self, name, description, lineno=0):
        self.lineno = lineno
        self.name = name
        self.description = description

    def children(self):
        nodelist = []
        if self.description:
            nodelist.append(self.description)
        return tuple(nodelist)


class Description(Node):
    attr_names = ()

    def __init__(self, definitions, lineno=0):
        self.lineno = lineno
        self.definitions = definitions

    def children(self):
        nodelist = []
        if self.definitions:
            nodelist.extend(self.definitions)
        return tuple(nodelist)


class ModuleDef(Node):
    attr_names = ('name',)

    def __init__(self, name, paramlist, portlist, items, default_nettype='wire', lineno=0):
        self.lineno = lineno
        self.name = name
        self.paramlist = paramlist
        self.portlist = portlist
        self.items = items
        self.default_nettype = default_nettype

    def children(self):
        nodelist = []
        if self.paramlist:
            nodelist.append(self.paramlist)
        if self.portlist:
            nodelist.append(self.portlist)
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)


class Paramlist(Node):
    attr_names = ()

    def __init__(self, params, lineno=0):
        self.lineno = lineno
        self.params = params

    def children(self):
        nodelist = []
        if self.params:
            nodelist.extend(self.params)
        return tuple(nodelist)


class Portlist(Node):
    attr_names = ()

    def __init__(self, ports, lineno=0):
        self.lineno = lineno
        self.ports = ports

    def children(self):
        nodelist = []
        if self.ports:
            nodelist.extend(self.ports)
        return tuple(nodelist)


# pdims: Packed Dimensions
# udims: Unpacked Dimensions
# {pdims} {width} name {udims}

class Port(Node):
    attr_names = ('name', 'type',)

    def __init__(self, name, width, pdims, udims, type, lineno=0):
        self.lineno = lineno
        self.name = name
        self.width = width
        self.pdims = pdims
        self.udims = udims
        self.type = type

    def children(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        if self.pdims:
            nodelist.append(self.pdims)
        if self.udims:
            nodelist.append(self.udims)
        return tuple(nodelist)


class Width(Node):
    attr_names = ()

    def __init__(self, msb, lsb=None, lineno=0):
        self.lineno = lineno
        self.msb = msb
        self.lsb = lsb

    def children(self):
        nodelist = []
        if self.msb:
            nodelist.append(self.msb)
        if self.lsb:
            nodelist.append(self.lsb)
        return tuple(nodelist)


class Length(Width):
    pass


class Dims(Node):
    attr_names = ()

    def __init__(self, lengths, lineno=0):
        self.lineno = lineno
        self.lengths = lengths

    def children(self):
        nodelist = []
        if self.lengths:
            nodelist.extend(self.lengths)
        return tuple(nodelist)


class Identifier(Node):
    attr_names = ('name',)

    def __init__(self, name, scope=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.scope = scope

    def children(self):
        nodelist = []
        if self.scope:
            nodelist.append(self.scope)
        return tuple(nodelist)

    def __repr__(self):
        if self.scope is None:
            return self.name
        return self.scope.__repr__() + '.' + self.name


class _Value(Node):
    attr_names = ()

    def __init__(self, value, lineno=0):
        self.lineno = lineno
        self.value = value

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)


class _Constant(_Value):
    attr_names = ('value',)

    def __init__(self, value, lineno=0):
        self.lineno = lineno
        self.value = value

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __repr__(self):
        return str(self.value)


class IntConst(_Constant):
    pass


class FloatConst(_Constant):
    pass


class StringConst(_Constant):
    pass


class _Variable(_Value):
    attr_names = ('name', 'signed')

    def __init__(self, name, width=None, signed=False, pdims=None, udims=None, value=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.width = width
        self.signed = signed
        self.pdims = pdims
        self.udims = udims
        self.value = value

    def children(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        if self.pdims:
            nodelist.append(self.pdims)
        if self.udims:
            nodelist.append(self.udims)
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)


class _Variable4State(_Variable):
    pass


class _Variable2State(_Variable):
    pass


class _VariableReal(_Variable):
    pass


class Input(_Variable4State):
    pass


class Output(_Variable4State):
    pass


class Inout(_Variable4State):
    pass


class Tri(_Variable4State):
    pass


class Wire(_Variable4State):
    pass


class Reg(_Variable4State):
    pass


class Integer(_Variable4State):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('31', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable4State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class Time(_Variable4State):

    def __init__(self, name, signed=False, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('64', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable4State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class Real(_VariableReal):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('63', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable4State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class RealTime(_VariableReal):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('63', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable4State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class Logic(_Variable4State):
    pass


class ShortInt(_Variable2State):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('16', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable2State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class Int(_Variable2State):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('31', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable2State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class LongInt(_Variable2State):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('63', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable2State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class Byte(_Variable2State):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('7', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable2State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class Bit(_Variable2State):
    pass


class ShortReal(_VariableReal):

    def __init__(self, name, signed=True, pdims=None, udims=None, value=None, lineno=0):
        width = Width(msb=IntConst('31', lineno=lineno), lsb=IntConst('0', lineno=lineno))
        _Variable4State.__init__(self, name, width, signed, pdims, udims, value, lineno)


class CustomVariable(_Variable):
    attr_names = ('name', 'typename', 'modportname')

    def __init__(self, typename, name, modportname=None, width=None, signed=False,
                 pdims=None, udims=None, value=None, lineno=0):
        _Variable.__init__(self, name, width, signed, pdims, udims, value, lineno)
        self.typename = typename
        self.modportname = modportname


class Ioport(Node):
    attr_names = ()

    def __init__(self, first, second=None, lineno=0):
        self.lineno = lineno
        self.first = first
        self.second = second

    def children(self):
        nodelist = []
        if self.first:
            nodelist.append(self.first)
        if self.second:
            nodelist.append(self.second)
        return tuple(nodelist)


class Parameter(Node):
    attr_names = ('name', 'signed')

    def __init__(self, name, value, width=None, pdims=None, udims=None, signed=False, lineno=0):
        self.lineno = lineno
        self.name = name
        self.value = value
        self.width = width
        self.signed = signed
        self.pdims = pdims
        self.udims = udims

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        if self.width:
            nodelist.append(self.width)
        if self.pdims:
            nodelist.append(self.pdims)
        if self.udims:
            nodelist.append(self.udims)
        return tuple(nodelist)


class Localparam(Parameter):
    pass


class Supply(Parameter):
    pass


class Decl(Node):
    attr_names = ()

    def __init__(self, list, lineno=0):
        self.lineno = lineno
        self.list = list

    def children(self):
        nodelist = []
        if self.list:
            nodelist.extend(self.list)
        return tuple(nodelist)


class Concat(Node):
    attr_names = ()

    def __init__(self, list, lineno=0):
        self.lineno = lineno
        self.list = list

    def children(self):
        nodelist = []
        if self.list:
            nodelist.extend(self.list)
        return tuple(nodelist)


class LConcat(Concat):
    pass


class Repeat(Node):
    attr_names = ()

    def __init__(self, value, times, lineno=0):
        self.lineno = lineno
        self.value = value
        self.times = times

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        if self.times:
            nodelist.append(self.times)
        return tuple(nodelist)


class Partselect(Node):
    attr_names = ()

    def __init__(self, var, msb, lsb, lineno=0):
        self.lineno = lineno
        self.var = var
        self.msb = msb
        self.lsb = lsb

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        if self.msb:
            nodelist.append(self.msb)
        if self.lsb:
            nodelist.append(self.lsb)
        return tuple(nodelist)


class Pointer(Node):
    attr_names = ()

    def __init__(self, var, ptr, lineno=0):
        self.lineno = lineno
        self.var = var
        self.ptr = ptr

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        if self.ptr:
            nodelist.append(self.ptr)
        return tuple(nodelist)


class Lvalue(Node):
    attr_names = ()

    def __init__(self, var, lineno=0):
        self.lineno = lineno
        self.var = var

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        return tuple(nodelist)


class Rvalue(Node):
    attr_names = ()

    def __init__(self, var, lineno=0):
        self.lineno = lineno
        self.var = var

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        return tuple(nodelist)


# ------------------------------------------------------------------------------
class _Operator(Node):
    attr_names = ()

    def __init__(self, left, right, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right

    def children(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)

    def __repr__(self):
        ret = '(' + self.__class__.__name__
        for c in self.children():
            ret += ' ' + c.__repr__()
        ret += ')'
        return ret


class _BinaryOperator(_Operator):
    pass


class _UnaryOperator(_Operator):
    attr_names = ()

    def __init__(self, right, lineno=0):
        self.lineno = lineno
        self.right = right

    def children(self):
        nodelist = []
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)


# Level 1 (Highest Priority)
class Uplus(_UnaryOperator):
    pass


class Uminus(_UnaryOperator):
    pass


class Ulnot(_UnaryOperator):
    pass


class Unot(_UnaryOperator):
    pass


class Uand(_UnaryOperator):
    pass


class Unand(_UnaryOperator):
    pass


class Uor(_UnaryOperator):
    pass


class Unor(_UnaryOperator):
    pass


class Uxor(_UnaryOperator):
    pass


class Uxnor(_UnaryOperator):
    pass


# Level 2
class Power(_BinaryOperator):
    pass


class Times(_BinaryOperator):
    pass


class Divide(_BinaryOperator):
    pass


class Mod(_BinaryOperator):
    pass


# Level 3
class Plus(_BinaryOperator):
    pass


class Minus(_BinaryOperator):
    pass


# Level 4
class Sll(_BinaryOperator):
    pass


class Srl(_BinaryOperator):
    pass


class Sla(_BinaryOperator):
    pass


class Sra(_BinaryOperator):
    pass


# Level 5
class LessThan(_BinaryOperator):
    pass


class GreaterThan(_BinaryOperator):
    pass


class LessEq(_BinaryOperator):
    pass


class GreaterEq(_BinaryOperator):
    pass


# Level 6
class Eq(_BinaryOperator):
    pass


class NotEq(_BinaryOperator):
    pass


class Eql(_BinaryOperator):
    pass  # ===


class NotEql(_BinaryOperator):
    pass  # !==


# Level 7
class And(_BinaryOperator):
    pass


class Xor(_BinaryOperator):
    pass


class Xnor(_BinaryOperator):
    pass


# Level 8
class Or(_BinaryOperator):
    pass


# Level 9
class Land(_BinaryOperator):
    pass


# Level 10
class Lor(_BinaryOperator):
    pass


# Level 11
class Cond(_Operator):
    attr_names = ()

    def __init__(self, cond, true_value, false_value, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.true_value = true_value
        self.false_value = false_value

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.true_value:
            nodelist.append(self.true_value)
        if self.false_value:
            nodelist.append(self.false_value)
        return tuple(nodelist)


class TypeCast(_Operator):
    attr_names = ('casting_type',)

    def __init__(self, casting_type, right, lineno=0):
        self.lineno = lineno
        self.casting_type = casting_type
        self.right = right

    def children(self):
        nodelist = []
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)


class WidthCast(_Operator):
    attr_names = ()

    def __init__(self, width, right, lineno=0):
        self.lineno = lineno
        self.width = width
        self.right = right

    def children(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)


class Assign(Node):
    attr_names = ()

    def __init__(self, left, right, ldelay=None, rdelay=None, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay

    def children(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        if self.ldelay:
            nodelist.append(self.ldelay)
        if self.rdelay:
            nodelist.append(self.rdelay)
        return tuple(nodelist)


class Always(Node):
    attr_names = ()

    def __init__(self, sens_list, statement, lineno=0):
        self.lineno = lineno
        self.sens_list = sens_list
        self.statement = statement

    def children(self):
        nodelist = []
        if self.sens_list:
            nodelist.append(self.sens_list)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class AlwaysFF(Always):
    pass


class AlwaysComb(Always):
    pass


class AlwaysLatch(Always):
    pass


class SensList(Node):
    attr_names = ()

    def __init__(self, list, lineno=0):
        self.lineno = lineno
        self.list = list

    def children(self):
        nodelist = []
        if self.list:
            nodelist.extend(self.list)
        return tuple(nodelist)


class Sens(Node):
    attr_names = ('type',)

    def __init__(self, sig, type='posedge', lineno=0):
        self.lineno = lineno
        self.sig = sig
        self.type = type  # 'posedge', 'negedge', 'level', 'all' (*)

    def children(self):
        nodelist = []
        if self.sig:
            nodelist.append(self.sig)
        return tuple(nodelist)


class Substitution(Node):
    attr_names = ()

    def __init__(self, left, right, ldelay=None, rdelay=None, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay

    def children(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        if self.ldelay:
            nodelist.append(self.ldelay)
        if self.rdelay:
            nodelist.append(self.rdelay)
        return tuple(nodelist)


class BlockingSubstitution(Substitution):
    pass


class NonblockingSubstitution(Substitution):
    pass


class _SubstitutionOperator(BlockingSubstitution):

    def __init__(self, left, right, ldelay=None, rdelay=None, lineno=0):
        BlockingSubstitution.__init__(self, left, right, ldelay, rdelay, lineno)

    def children(self):
        return BlockingSubstitution.children(self)


class PlusEquals(_SubstitutionOperator):
    pass


class MinusEquals(_SubstitutionOperator):
    pass


class TimesEquals(_SubstitutionOperator):
    pass


class DivideEquals(_SubstitutionOperator):
    pass


class ModEquals(_SubstitutionOperator):
    pass


class OrEquals(_SubstitutionOperator):
    pass


class AndEquals(_SubstitutionOperator):
    pass


class XorEquals(_SubstitutionOperator):
    pass


class SlaEquals(_SubstitutionOperator):
    pass


class SraEquals(_SubstitutionOperator):
    pass


class SllEquals(_SubstitutionOperator):
    pass


class SrlEquals(_SubstitutionOperator):
    pass


class Increment(_SubstitutionOperator):

    def __init__(self, left, lineno=0):
        right = IntConst('1', lineno=lineno)
        ldelay = None
        rdelay = None
        _SubstitutionOperator.__init__(self, left, right, ldelay, rdelay, lineno)


class Decrement(_SubstitutionOperator):

    def __init__(self, left, lineno=0):
        right = IntConst('1', lineno=lineno)
        ldelay = None
        rdelay = None
        _SubstitutionOperator.__init__(self, left, right, ldelay, rdelay, lineno)


class IfStatement(Node):
    attr_names = ()

    def __init__(self, cond, true_statement, false_statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.true_statement = true_statement
        self.false_statement = false_statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.true_statement:
            nodelist.append(self.true_statement)
        if self.false_statement:
            nodelist.append(self.false_statement)
        return tuple(nodelist)


class PriorityIf(IfStatement):
    pass


class ForStatement(Node):
    attr_names = ()

    def __init__(self, pre, cond, post, statement, lineno=0):
        self.lineno = lineno
        self.pre = pre
        self.cond = cond
        self.post = post
        self.statement = statement

    def children(self):
        nodelist = []
        if self.pre:
            nodelist.append(self.pre)
        if self.cond:
            nodelist.append(self.cond)
        if self.post:
            nodelist.append(self.post)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class WhileStatement(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class CaseStatement(Node):
    attr_names = ()

    def __init__(self, comp, caselist, lineno=0):
        self.lineno = lineno
        self.comp = comp
        self.caselist = caselist

    def children(self):
        nodelist = []
        if self.comp:
            nodelist.append(self.comp)
        if self.caselist:
            nodelist.extend(self.caselist)
        return tuple(nodelist)


class CasexStatement(CaseStatement):
    pass


class CasezStatement(CaseStatement):
    pass


class UniqueCaseStatement(CaseStatement):
    pass


class Case(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.extend(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class Block(Node):
    attr_names = ('scope',)

    def __init__(self, statements, scope=None, lineno=0):
        self.lineno = lineno
        self.statements = statements
        self.scope = scope

    def children(self):
        nodelist = []
        if self.statements:
            nodelist.extend(self.statements)
        return tuple(nodelist)


class Initial(Node):
    attr_names = ()

    def __init__(self, statement, lineno=0):
        self.lineno = lineno
        self.statement = statement

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class EventStatement(Node):
    attr_names = ()

    def __init__(self, senslist, lineno=0):
        self.lineno = lineno
        self.senslist = senslist

    def children(self):
        nodelist = []
        if self.senslist:
            nodelist.append(self.senslist)
        return tuple(nodelist)


class WaitStatement(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class ForeverStatement(Node):
    attr_names = ()

    def __init__(self, statement, lineno=0):
        self.lineno = lineno
        self.statement = statement

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class DelayStatement(Node):
    attr_names = ()

    def __init__(self, delay, lineno=0):
        self.lineno = lineno
        self.delay = delay

    def children(self):
        nodelist = []
        if self.delay:
            nodelist.append(self.delay)
        return tuple(nodelist)


class InstanceList(Node):
    attr_names = ('module',)

    def __init__(self, module, parameterlist, instances, lineno=0):
        self.lineno = lineno
        self.module = module
        self.parameterlist = parameterlist
        self.instances = instances

    def children(self):
        nodelist = []
        if self.parameterlist:
            nodelist.extend(self.parameterlist)
        if self.instances:
            nodelist.extend(self.instances)
        return tuple(nodelist)


class Instance(Node):
    attr_names = ('name', 'module')

    def __init__(self, module, name, portlist, parameterlist, array=None, lineno=0):
        self.lineno = lineno
        self.module = module
        self.name = name
        self.portlist = portlist
        self.parameterlist = parameterlist
        self.array = array

    def children(self):
        nodelist = []
        if self.array:
            nodelist.append(self.array)
        if self.parameterlist:
            nodelist.extend(self.parameterlist)
        if self.portlist:
            nodelist.extend(self.portlist)
        return tuple(nodelist)


class ParamArg(Node):
    attr_names = ('paramname',)

    def __init__(self, paramname, argname, lineno=0):
        self.lineno = lineno
        self.paramname = paramname
        self.argname = argname

    def children(self):
        nodelist = []
        if self.argname:
            nodelist.append(self.argname)
        return tuple(nodelist)


class PortArg(Node):
    attr_names = ('portname',)

    def __init__(self, portname, argname, lineno=0):
        self.lineno = lineno
        self.portname = portname
        self.argname = argname

    def children(self):
        nodelist = []
        if self.argname:
            nodelist.append(self.argname)
        return tuple(nodelist)


class Function(Node):
    attr_names = ('name', 'automatic')

    def __init__(self, name, retwidth, statement, automatic=False, lineno=0):
        self.lineno = lineno
        self.name = name
        self.retwidth = retwidth
        self.statement = statement
        self.automatic = automatic

    def children(self):
        nodelist = []
        if self.retwidth:
            nodelist.append(self.retwidth)
        if self.statement:
            nodelist.extend(self.statement)
        return tuple(nodelist)

    def __repr__(self):
        return self.name.__repr__()


class FunctionCall(Node):
    attr_names = ()

    def __init__(self, name, args, lineno=0):
        self.lineno = lineno
        self.name = name
        self.args = args

    def children(self):
        nodelist = []
        if self.name:
            nodelist.append(self.name)
        if self.args:
            nodelist.extend(self.args)
        return tuple(nodelist)

    def __repr__(self):
        return self.name.__repr__()


class Task(Node):
    attr_names = ('name', 'automatic')

    def __init__(self, name, statement, automatic=False, lineno=0):
        self.lineno = lineno
        self.name = name
        self.statement = statement
        self.automatic = automatic

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.extend(self.statement)
        return tuple(nodelist)


class TaskCall(Node):
    attr_names = ()

    def __init__(self, name, args, lineno=0):
        self.lineno = lineno
        self.name = name
        self.args = args

    def children(self):
        nodelist = []
        if self.name:
            nodelist.append(self.name)
        if self.args:
            nodelist.extend(self.args)
        return tuple(nodelist)


class GenerateStatement(Node):
    attr_names = ()

    def __init__(self, items, lineno=0):
        self.lineno = lineno
        self.items = items

    def children(self):
        nodelist = []
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)


class Genvar(_Variable):
    pass


class SystemCall(Node):
    attr_names = ('syscall',)

    def __init__(self, syscall, args, lineno=0):
        self.lineno = lineno
        self.syscall = syscall
        self.args = args

    def children(self):
        nodelist = []
        if self.args:
            nodelist.extend(self.args)
        return tuple(nodelist)

    def __repr__(self):
        ret = []
        ret.append('(')
        ret.append('$')
        ret.append(self.syscall)
        for a in self.args:
            ret.append(' ')
            ret.append(str(a))
        ret.append(')')
        return ''.join(ret)


class IdentifierScopeLabel(Node):
    attr_names = ('name', 'loop')

    def __init__(self, name, loop=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.loop = loop

    def children(self):
        nodelist = []
        return tuple(nodelist)


class IdentifierScope(Node):
    attr_names = ()

    def __init__(self, labellist, lineno=0):
        self.lineno = lineno
        self.labellist = labellist

    def children(self):
        nodelist = []
        if self.labellist:
            nodelist.extend(self.labellist)
        return tuple(nodelist)


class Pragma(Node):
    attr_names = ()

    def __init__(self, entry, lineno=0):
        self.lineno = lineno
        self.entry = entry

    def children(self):
        nodelist = []
        if self.entry:
            nodelist.append(self.entry)
        return tuple(nodelist)


class PragmaEntry(Node):
    attr_names = ('name', )

    def __init__(self, name, value=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.value = value

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)


class Disable(Node):
    attr_names = ('dest',)

    def __init__(self, dest, lineno=0):
        self.lineno = lineno
        self.dest = dest

    def children(self):
        nodelist = []
        return tuple(nodelist)


class ParallelBlock(Node):
    attr_names = ('scope',)

    def __init__(self, statements, scope=None, lineno=0):
        self.lineno = lineno
        self.statements = statements
        self.scope = scope

    def children(self):
        nodelist = []
        if self.statements:
            nodelist.extend(self.statements)
        return tuple(nodelist)


class SingleStatement(Node):
    attr_names = ()

    def __init__(self, statement, lineno=0):
        self.lineno = lineno
        self.statement = statement

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class Interface(Node):
    attr_names = ('name',)

    def __init__(self, name, paramlist, portlist, items, lineno=0):
        self.lineno = lineno
        self.name = name
        self.paramlist = paramlist
        self.portlist = portlist
        self.items = items

    def children(self):
        nodelist = []
        if self.paramlist:
            nodelist.append(self.paramlist)
        if self.portlist:
            nodelist.append(self.portlist)
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)


class Modport(Node):
    attr_names = ('name',)

    def __init__(self, name, ports, lineno=0):
        self.lineno = lineno
        self.name = name
        self.ports = ports

    def children(self):
        nodelist = []
        if self.ports:
            nodelist.extend(self.ports)
        return tuple(nodelist)


class Struct(Node):
    attr_names = ('name', 'packed')

    def __init__(self, name, items, packed=False, lineno=0):
        self.lineno = lineno
        self.name = name
        self.items = items
        self.packed = packed

    def children(self):
        nodelist = []
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)


class Union(Node):
    attr_names = ('name', 'packed')

    def __init__(self, name, items, packed=False, lineno=0):
        self.lineno = lineno
        self.name = name
        self.items = items
        self.packed = packed

    def children(self):
        nodelist = []
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)


class Enum(Node):
    attr_names = ('name',)

    def __init__(self, name, enumlist, lineno=0):
        self.lineno = lineno
        self.name = name
        self.enumlist = enumlist

    def children(self):
        nodelist = []
        if self.enumlist:
            nodelist.append(self.enumlist)
        return tuple(nodelist)


class Enumlist(Node):
    attr_names = ('name',)

    def __init__(self, items=None,
                 name=None, length=None, start=None, end=None, value=None,
                 lineno=0):
        self.lineno = lineno
        self.items = items
        self.name = name
        self.length = length
        self.start = start
        self.end = end
        self.value = value

    def children(self):
        nodelist = []
        if self.items:
            nodelist.extend(self.items)
        if self.length:
            nodelist.append(self.length)
        if self.start:
            nodelist.append(self.start)
        if self.end:
            nodelist.append(self.end)
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)


class TypeDef(Node):
    attr_names = ('name', 'types')

    def __init__(self, name, types, width=None, pdims=None, udims=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.types = types
        self.width = width
        self.pdims = pdims
        self.udims = udims

    def children(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        if self.pdims:
            nodelist.append(self.pdims)
        if self.udims:
            nodelist.append(self.udims)
        return tuple(nodelist)


class EmbeddedCode(Node):
    attr_names = ('code',)

    def __init__(self, code, lineno=0):
        self.code = code

    def children(self):
        nodelist = []
        return tuple(nodelist)
