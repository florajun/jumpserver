
class Choice(str):
    def __new__(cls, value, label):
        self = super().__new__(cls, value)
        self.label = label
        return self


class ChoiceSetType(type):
    def __new__(cls, name, bases, attrs):
        _choices = []
        collected = set()
        new_attrs = {}
        for k, v in attrs.items():
            if isinstance(v, tuple):
                v = Choice(*v)
                assert v not in collected, 'Cannot be defined repeatedly'
                _choices.append(v)
                collected.add(v)
            new_attrs[k] = v
        for base in bases:
            if hasattr(base, '_choices'):
                for c in base._choices:
                    if c not in collected:
                        _choices.append(c)
                        collected.add(c)
        new_attrs['_choices'] = _choices
        new_attrs['choices'] = [(c, c.label) for c in _choices]
        return type.__new__(cls, name, bases, new_attrs)


class ChoiceSet(metaclass=ChoiceSetType):
    choices = None  # 用于 Django Model 中的 choices 配置， 为了代码提示在此声明
