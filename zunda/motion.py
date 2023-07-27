import bisect
import math
from typing import Optional, Sequence, TypeVar, Generic, Tuple, Callable

motion_types_to_func = {
    'linear': lambda t: t,
    'ease_in': lambda t: t ** 2,
    'ease_out': lambda t: 1. - (1. - t) ** 2,
    'ease_in_out': lambda t: t ** 2 * (3. - 2. * t),
    'ease_in_cubic': lambda t: t ** 3,
    'ease_out_cubic': lambda t: 1. - (1. - t) ** 3,
    'ease_in_expo': lambda t: math.exp(- 10. * (1 - t)),
    'ease_out_expo': lambda t: 1 - math.exp(- 10. * t),
}

T = TypeVar('T', float, Tuple[float, float])


class Motion(Generic[T]):

    def __init__(self, default_value: Optional[T] = None):
        self.keyframes: list[float] = []
        self.values: list[T] = []
        self.motion_types: list[Callable[[float], float]] = []
        self.default_value: Optional[T] = default_value

    def __call__(self, layer_time: float) -> T:
        if len(self.keyframes) == 0:
            if self.default_value is not None:
                return self.default_value
            raise ValueError('No keyframes')
        elif len(self.keyframes) == 1:
            return self.values[0]

        if layer_time < self.keyframes[0]:
            return self.values[0]
        elif self.keyframes[-1] <= layer_time:
            return self.values[-1]
        else:
            i = bisect.bisect(self.keyframes, layer_time)
            m, M = self.values[i - 1], self.values[i]
            duration = self.keyframes[i] - self.keyframes[i - 1]
            t = (layer_time - self.keyframes[i - 1]) / duration
            t = self.motion_types[i - 1](t)
            if isinstance(m, float) and isinstance(M, float):
                return float(m + (M - m) * t)
            elif isinstance(m, tuple) and isinstance(M, tuple):
                return (m[0] + (M[0] - m[0]) * t, m[1] + (M[1] - m[1]) * t)
            else:
                raise ValueError(f'Unexpected value: {m}, {M}')

    def _cast(self, value: T) -> T:
        if isinstance(value, tuple):
            return (float(value[0]), float(value[1]))
        else:
            return float(value)

    def append(self, keyframe: float, value: T, motion_type: str = 'linear') -> 'Motion[T]':
        i = bisect.bisect(self.keyframes, keyframe)
        self.keyframes.insert(i, float(keyframe))
        self.values.insert(i, self._cast(value))
        self.motion_types.insert(i, motion_types_to_func[motion_type])
        return self

    def extend(self, keyframes: Sequence[float], values: list[T], motion_types: Optional[Sequence[str]] = None) -> 'Motion[T]':
        assert len(keyframes) == len(values)
        if motion_types is not None:
            assert len(keyframes) == len(motion_types)
        motion_types = ['linear'] * len(keyframes) if motion_types is None else motion_types
        keyframes = self.keyframes + [float(k) for k in keyframes]
        values = self.values + [self._cast(v) for v in values]
        motion_types = self.motion_types + [motion_types_to_func[t] for t in motion_types]
        zipped = sorted(zip(keyframes, values, motion_types))
        keyframes_sorted, values_sorted, motion_types_sorted = zip(*zipped)
        self.keyframes = keyframes_sorted
        self.values = values_sorted
        self.motion_types = motion_types_sorted
        return self
