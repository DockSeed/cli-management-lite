from textual.widgets import Select
import inspect

print('Select.__init__:', inspect.signature(Select.__init__))
# create instance with minimal args
s = Select(options=[('A','1')], value='1', id='sel')
print('Has attributes:', [a for a in dir(s) if not a.startswith('_')])
print('value:', s.value)
print('BLANK attr:', getattr(Select, 'BLANK', None))

