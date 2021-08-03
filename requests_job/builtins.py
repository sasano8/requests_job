from .utils import _eval_builtins

__locals__ = locals()

for k, v in _eval_builtins.items():
    exec(f"{k}")
    __locals__[k] = v

del __locals__
del _eval_builtins
