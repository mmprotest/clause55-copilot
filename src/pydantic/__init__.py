"""Lightweight Pydantic-style utilities for offline environments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T")


class _Missing:
    pass


MISSING = _Missing()


@dataclass
class FieldInfo:
    default: Any = MISSING
    default_factory: Optional[Callable[[], Any]] = None
    metadata: Dict[str, Any] = None


def Field(*, default: Any = MISSING, default_factory: Callable[[], Any] | None = None, **metadata: Any) -> FieldInfo:
    return FieldInfo(default=default, default_factory=default_factory, metadata=metadata)


def _resolve_default(value: Any) -> Any:
    if isinstance(value, FieldInfo):
        if value.default is not MISSING:
            return value.default
        if value.default_factory is not None:
            return value.default_factory()
        return None
    return value


def field_validator(*fields: str):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func.__field_validators__ = fields
        return func

    return decorator


class BaseModel:
    __validators__: Dict[str, List[Callable[..., Any]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        validators: Dict[str, List[Callable[..., Any]]] = {}
        for base in reversed(cls.__mro__):
            base_validators = getattr(base, "__validators__", {})
            for field, funcs in base_validators.items():
                validators.setdefault(field, []).extend(funcs)
        for attr in cls.__dict__.values():
            func = None
            if isinstance(attr, classmethod):
                func = attr.__func__
            elif callable(attr):
                func = attr
            if func is not None and hasattr(func, "__field_validators__"):
                for field in getattr(func, "__field_validators__"):
                    validators.setdefault(field, []).append(func)
        cls.__validators__ = validators

    def __init__(self, **data: Any) -> None:
        hints = get_type_hints(self.__class__)
        for name, hint in hints.items():
            if name.startswith("_"):
                continue
            if name in data:
                value = data[name]
            else:
                value = _resolve_default(getattr(self.__class__, name, None))
            value = self._convert_value(name, value, hint)
            setattr(self, name, value)
        for extra_key, extra_value in data.items():
            if extra_key not in hints:
                setattr(self, extra_key, extra_value)

    @classmethod
    def model_validate(cls: Type[T], data: Any) -> T:
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict to validate {cls.__name__}")
        return cls(**data)

    def model_dump(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        hints = getattr(self.__class__, "__annotations__", {})
        for name in hints:
            result[name] = self._export_value(getattr(self, name))
        return result

    def _convert_value(self, name: str, value: Any, hint: Any) -> Any:
        origin = get_origin(hint)
        args = get_args(hint)
        if origin is Union:
            for option in args:
                if option is type(None) and value is None:
                    return None
                try:
                    return self._convert_value(name, value, option)
                except Exception:
                    continue
            return value
        if origin in {list, List}:
            item_type = args[0] if args else Any
            iterable = value or []
            return [self._convert_nested(item_type, item) for item in iterable]
        if origin in {tuple, Tuple}:
            item_type = args[0] if args else Any
            if args and len(args) == 2 and args[1] is Ellipsis:
                return tuple(self._convert_nested(item_type, item) for item in value)
            return tuple(value)
        if origin in {dict, Dict}:
            key_type, value_type = args if len(args) == 2 else (Any, Any)
            return {
                self._convert_nested(key_type, k): self._convert_nested(value_type, v)
                for k, v in (value or {}).items()
            }
        converted = self._convert_nested(hint, value)
        for validator in self.__class__.__validators__.get(name, []):
            if isinstance(validator, classmethod):
                converted = validator.__func__(self.__class__, converted, values=self.__dict__)
            else:
                converted = validator(self.__class__, converted, values=self.__dict__)
        return converted

    def _convert_nested(self, hint: Any, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, FieldInfo):
            value = _resolve_default(value)
        if isinstance(hint, type) and issubclass(hint, BaseModel):
            return hint.model_validate(value)
        if hint in {int, float, str, bool}:
            return hint(value)
        return value

    def _export_value(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, list):
            return [self._export_value(item) for item in value]
        if isinstance(value, tuple):
            return [self._export_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self._export_value(val) for key, val in value.items()}
        return value


class RootModel(BaseModel):
    root: Any

    def __init__(self, root: Any):
        super().__setattr__("root", root)

    def model_dump(self) -> Any:
        return self.root


__all__ = ["BaseModel", "Field", "RootModel", "field_validator"]

