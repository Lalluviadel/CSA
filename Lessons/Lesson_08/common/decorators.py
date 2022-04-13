import inspect


class Log:

    def __call__(self, decorated_cls):
        """Получаем декорируемый класс"""

        def log_decorator(decorated_foo):
            """Получаем метод декорируемого класса"""

            def foo_decorator(self, *args, **kwargs):
                """Добавляем логирование"""
                source_foo = decorated_foo(self, *args, **kwargs)
                self.logger.debug(f'Вызов функции {decorated_foo.__name__} c параметрами {args}, {kwargs} '
                                  f'из модуля {decorated_foo.__module__}, из функции {inspect.stack()[1][3]}',
                                  stacklevel=2)
                return source_foo

            return foo_decorator

        for method in decorated_cls.__dict__:
            """Снабжаем каждый публичный метод класса нашим декоратором"""
            if callable(getattr(decorated_cls, method)) and not method.startswith('_'):
                setattr(decorated_cls, method, log_decorator(getattr(decorated_cls, method)))
        return decorated_cls
