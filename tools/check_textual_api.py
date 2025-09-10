import inspect
from textual.app import App

sig = inspect.signature(App.push_screen)
print("push_screen signature:", sig)
params = list(sig.parameters)
print("params:", params)
print("has callback:", "callback" in params)

