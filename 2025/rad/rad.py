# Basic reverse-mode automatic differentiation in Python. Create expressions
# out of Var objects, then call grad() on the final result to backpropagate.
# See the examples in the __main__ block at the end of the file.
#
# Eli Bendersky (https://eli.thegreenplace.net)
# This code is in the public domain
import math
from dataclasses import dataclass


@dataclass
class Predecessor:
    multiplier: float
    var: "Var"


class Var:
    def __init__(self, v):
        self.v = v
        self.predecessors = []
        self.gv = 0.0

    def __add__(self, other):
        other = ensure_var(other)
        out = Var(self.v + other.v)
        out.predecessors.append(Predecessor(1.0, self))
        out.predecessors.append(Predecessor(1.0, other))
        return out

    def __radd__(self, other):
        return self + other

    def __neg__(self):
        out = Var(-self.v)
        out.predecessors.append(Predecessor(-1.0, self))
        return out

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return other + (-self)

    def __mul__(self, other):
        other = ensure_var(other)
        out = Var(self.v * other.v)
        out.predecessors.append(Predecessor(other.v, self))
        out.predecessors.append(Predecessor(self.v, other))
        return out

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        return div(self, other)

    def __rtruediv__(self, other):
        return div(other, self)

    def grad(self, gv):
        self.gv += gv
        for p in self.predecessors:
            p.var.grad(p.multiplier * gv)


def ensure_var(v):
    if isinstance(v, Var):
        return v
    return Var(v)


def div(x, y):
    """x / y"""
    x = ensure_var(x)
    y = ensure_var(y)
    out = Var(x.v / y.v)
    out.predecessors.append(Predecessor(1.0 / y.v, x))
    out.predecessors.append(Predecessor(-x.v / (y.v**2), y))
    return out


def exp(x):
    """e^x"""
    x = ensure_var(x)
    out = Var(math.exp(x.v))
    out.predecessors.append(Predecessor(math.exp(x.v), x))
    return out


def log(x):
    """log(x) - natural logarithm of x"""
    x = ensure_var(x)
    out = Var(math.log(x.v))
    out.predecessors.append(Predecessor(1.0 / x.v, x))
    return out


def sin(x):
    """sin(x)"""
    x = ensure_var(x)
    out = Var(math.sin(x.v))

    out.predecessors.append(Predecessor(math.cos(x.v), x))
    return out


if __name__ == "__main__":
    # Examples of expressions created our of Var notes and operations they
    # support, followed by calling grad(). After calling grad(), the
    # participating Vars should not be reused.
    xx = Var(0.5)
    sigmoid = 1 / (1 + exp(-xx))
    print(f"xx={xx.v}, sigmoid={sigmoid.v}")

    sigmoid.grad(1.0)
    print(f"dsigmoid/dxx = {xx.gv}")

    # Example from the paper "Automatic Differentiation in Machine Learning:
    # a Survey" by Baydin et al.
    x1 = Var(2)
    x2 = Var(5)
    f = log(x1) + x1 * x2 - sin(x2)
    print(f"x1={x1.v}, x2={x2.v}, f={f.v}")

    f.grad(1.0)
    print(f"df/dx1={x1.gv}, df/dx2={x2.gv}")
