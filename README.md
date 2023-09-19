![GitHub Logo](images/movis_logo.png)

# Movis: Video Editing as a Code

[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/rezoo/movis)
![Continuous integration](https://github.com/rezoo/movis/actions/workflows/python-package.yml/badge.svg)

## What is Movis?

Movis is an engine written in Python, purposed for video production tasks.
This library allows users to generate various types of videos,
including but not limited to presentation videos, explainer videos,
training videos, and game commentary videos, through Python.

### Library without GUI for automation

Contrary to many existing video production software solutions,
Movis does not offer a Graphical User Interface (GUI).
This may be perceived as a limitation for users new to video editing,
but it serves as an advantage for automation.
Specifically, engineers can
*integrate their own ML models to execute tasks* such as
facial image anonymization or automatic summarization of videos.

### Creating Video with Compositions

Similar to other video editing software,
Movis employs the concept of "compositions" as the fundamental unit for video editing.
Within a composition, users can include multiple layers and manipulate
these layers' attributes over a time scale to produce a video.
Effects can also be selectively applied to these layers as needed.

Here's some example code:

```python
import movis as mv

scene = mv.layer.Composition(size=(1920, 1080), duration=5.0)
scene.add_layer(mv.layer.Rectangle(scene.size, color='#fb4562'))

pos = scene.size[0] // 2, scene.size[1] // 2
scene.add_layer(
    mv.layer.Text('Hello World!', font_size=256, font_family='Helvetica', color='#ffffff'),
    name='text',  # The layer item can be accessed by name
    offset=1.0,  # Show the text after one second
    position=pos,  # The layer is centered by default, but it can also be specified explicitly
    opacity=1.0, scale=1.0, rotation=0.0,  # opacity, scale, and rotation are also supported
    blending_mode='normal')  # Blending mode can be specified for each layer.
scene['text'].add_effect(mv.effect.DropShadow(offset=10.0))  # Multiple effects can be added.
scene['text'].scale.enable_motion().extend(
    keyframes=[0.0, 1.0], values=[0.0, 1.0], motion_types=['ease_in_out'])
# Fade-in effect. It means that the text appears fully two seconds later.
scene['text'].opacity.enable_motion().extend([0.0, 1.0], [0.0, 1.0])

scene.write_video('output.mp4')
```

The composition can also be used as a layer.
By combining multiple compositions and layers, users can create complex videos.

### Implementation of custom layers, effects, and animations

Movis is engineered to facilitate the straightforward implementation of user-defined layers,
thereby enabling the seamless integration of unique visual effects into video projects.
This design obviates the necessity for users to possess
intricate knowledge of the library or to become proficient
in advanced programming languages exemplified by C++.
Thus, users may focus their attention predominantly on
their creative concepts.
In instances where accelerated computational performance is requisite,
one may employ separate, specialized libraries such as
Jax or PyTorch to execute computations at an elevated speed via a GPU.

For example, to implement a user-defined layer, you only need to create a function that, given a time,
returns an `np.ndarray` with a shape of `(H, W, 4)` and dtype of `np.uint8` in RGBA order, or returns `None`.

```python
import numpy as np
import movis as mv

size = (640, 480)

def get_radial_gradient_image(time: float) -> np.ndarray:
    if time < 0.:
        return None
    center = np.array([size[1] // 2, size[0] // 2])
    radius = min(size)
    inds = np.mgrid[:size[1], :size[0]] - center[:, None, None]
    r = np.sqrt((inds ** 2).sum(axis=0))
    p = 255 - (np.clip(r / radius, 0, 1) * 255).astype(np.uint8)
    img = np.zeros((size[1], size[0], 4), dtype=np.uint8)
    img[:, :, :3] = p[:, :, None]
    img[:, :, 3] = 255
    return img

scene = mv.layer.Composition(size, duration=5.0)
scene.add_layer(get_radial_gradient_image)
scene.write_video('output.mp4')
```

If you want to specify the duration of a layer,
the `duration` property is required. Movis also offers caching features
to accelerate rendering. If you wish to speed up rendering for layers
where the frame remains static, you can implement the `get_key(time: float)` method:

```python
class RadialGradientLayer:
    def __init__(self, size: tuple[int, int], duration: float):
        self.size = size
        self.duration = duration
        self.center = np.array([size[1] // 2, size[0] // 2])
    
    def get_key(self, time: float) -> Hashable:
        # Returns 0 since the same image is always returned
        return 0
    
    def __call__(self, time: float) -> None | np.ndarray:
        # ditto.
```

#### Custom effects

Effects for layers can also be implemented in a similar straightforward manner.

```python
import cv2
import movis as mv
import numpy as np

def apply_gaussian_blur(prev_image: np.ndarray, time: float) -> np.ndarray | None:
    return cv2.GaussianBlur(prev_image, (7, 7), -1)

scene = mv.layer.Composition(size=(1920, 1080), duration=5.0)
scene.add_layer(mv.layer.Rectangle(scene.size, color='#fb4562'))
scene.add_layer(
    mv.layer.Text('Hello World!', font_size=256, font_family='Helvetica', color='#ffffff'),
    name='text')
scene['text'].add_effect(apply_gaussian_blur)
```

#### User-defined animations

Animation can be set up on a keyframe basis, but in some cases,
users may want to animate using user-defined functions.
movis provides methods to handle such situations as well.

```python
import movis as mv
import numpy as np

scene = mv.layer.Composition(size=(1920, 1080), duration=5.0)
scene.add_layer(
    mv.layer.Text('Hello World!', font_size=256, font_family='Helvetica', color='#ffffff'),
    name='text')
scene['text'].position.add_function(
    lambda prev_value, time: prev_value + np.array([0, np.sin(time * 2 * np.pi) * 100]),
)
```

### Fast Prototyping in Jupyter Notebook

Jupyter notebooks are commonly used for data analysis that requires a lot of trial and error using Python.
Various methods for Jupyter notebooks are also included in movis to speed up the video production process.

For example, ``composition.render_and_play()`` is often used to
preview a section of a video within a Jupyter notebook.

```python
import movis as mv

scene = mv.layer.Composition(size=(1920, 1080), duration=10.0)
... # add layers and effects...
scene.render_and_play(
    start_time=5.0, end_time=10.0, preview_level=2)  # play the video from 5 to 10 seconds
```

This method has an argument called ``preview_level``.
For example, by setting it to 2, you can sacrifice video quality
by reducing the final resolution to 1/2 in exchange for faster rendering.

If you want to reduce the resolution when exporting videos or still images using
``composition.write_video()`` or similar methods,
you can use the syntax ``with composition.preview(level=2)``.

```python
import movis as mv

scene = mv.layer.Composition(size=(1920, 1080), duration=10.0)
... # add layers and effects...
with scene.preview(level=2):
    scene.write_video('output.mp4')  # The resolution of the output video is 1/2.
    img = scene(5.0)  # retrieve an image at t = 5.0
assert img.shape == (540, 960, 4)
```

Within this scope, the resolution of all videos and images will be reduced to 1/2.
This can be useful during the trial and error process.

## Installation

Movis is a pure Python library and can be installed via the Python Package Index:

```bash
# PyPI
$ pip install movis
```

We have confirmed that movis works with Python versions 3.9 to 3.11.

## License

MIT License (see `LICENSE` for details).
