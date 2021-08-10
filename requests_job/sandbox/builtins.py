from .builtins_data import eval_builtins

__locals__ = locals()

for k, v in eval_builtins.items():
    exec(f"{k}")
    __locals__[k] = v

del __locals__
del eval_builtins
