import hashlib
from pathlib import Path
from typing import Optional, Sequence, Union

import numpy as np
from PIL import Image as PILImage

from ..imgproc import alpha_composite
from ..layer.mixin import TimelineMixin

try:
    from pdf2image import convert_from_path
    pdf2image_available = True
except ImportError:
    pdf2image_available = False


class Slide(TimelineMixin):
    def __init__(
        self,
        start_times: Sequence[float],
        end_times: Sequence[float],
        slide_file: Union[str, Path],
        slide_counter: Sequence[int],
    ) -> None:
        if not pdf2image_available:
            raise ImportError("pdf2image is not installed")
        super().__init__(start_times, end_times)
        self.slide_timeline = np.cumsum(slide_counter)
        self.slide_file = slide_file
        self.slide_images: Optional[list[np.ndarray]] = None

    def get_key(self, time: float) -> int:
        idx = self.get_state(time)
        key = int(self.slide_timeline[idx]) if 0 < idx else -1
        return key

    def __call__(self, time: float) -> Optional[np.ndarray]:
        idx = self.get_state(time)
        if idx < 0:
            return None
        slide_number = self.slide_timeline[idx]
        if self.slide_images is None:
            slide_images = []
            for img in convert_from_path(self.slide_file):
                img_np = np.asarray(img.convert("RGBA"))
                slide_images.append(img_np)
            self.slide_images = slide_images
        return self.slide_images[slide_number]


class Character(TimelineMixin):
    def __init__(
        self,
        start_times: Sequence[float],
        end_times: Sequence[float],
        character_name: str,
        character_dir: Union[str, Path],
        characters: Sequence[str],
        character_status: Sequence[str],
        initial_status: str = "n",
        blink_per_minute: int = 3,
        blink_duration: float = 0.2,
    ) -> None:
        assert len(start_times) == len(characters) == len(character_status)
        super().__init__(start_times, end_times)
        self.character_name = character_name
        self.character_imgs: dict[str, Union[Path, np.ndarray]] = {}
        self.eye_imgs: dict[str, list[Union[Path, np.ndarray]]] = {}
        character_dir = Path(character_dir)
        emotions = set()
        for character, status in zip(characters, character_status):
            if character == character_name:
                emotions.add(status)
        emotions.add(initial_status)
        for emotion in emotions:
            path = Path(character_dir) / f"{emotion}.png"
            self.character_imgs[emotion] = path
            eye_path = Path(character_dir) / f"{emotion}.eye.png"
            if eye_path.exists():
                eyes: list[Union[Path, np.ndarray]] = [eye_path]
                for f in character_dir.iterdir():
                    x = f.name.split(".")
                    if f.name.startswith(f"{emotion}.eye.") and len(x) == 4:
                        eyes.append(f)
                self.eye_imgs[emotion] = eyes

        self.character_timeline: list[str] = []
        status = initial_status
        for current_character, current_status in zip(characters, character_status):
            if current_character == character_name:
                status = current_status
            self.character_timeline.append(status)

        self.blink_per_minute = blink_per_minute
        self.blink_duration = blink_duration

    def get_eye_state(self, time: float, idx: int) -> int:

        def rand_from_string(string: str, seed: int = 0) -> float:
            string = f"{seed}:{string}"
            s = hashlib.sha224(f"{seed}:{string}".encode("utf-8")).digest()
            x = np.frombuffer(s, dtype=np.uint32)[0]
            return np.random.RandomState(x).rand()

        emotion = self.character_timeline[idx]
        if emotion not in self.eye_imgs:
            return -1
        elif len(self.eye_imgs[emotion]) == 1:
            return 0
        p_threshold = self.blink_per_minute * self.blink_duration / 60
        n = int(time / self.blink_duration)
        p = rand_from_string(f"{self.character_name}:{n}")
        if p < p_threshold:
            frame_duration = self.blink_duration / (len(self.eye_imgs[emotion]) - 1)
            t1 = time - n * self.blink_duration
            n1 = int(t1 / frame_duration)
            return min(n1 + 1, len(self.eye_imgs[emotion]) - 1)
        else:
            return 0

    def get_key(self, time: float) -> tuple[str, int]:
        idx = self.get_state(time)
        if idx < 0:
            return ('', -1)
        emotion = self.character_timeline[idx]
        eye = self.get_eye_state(time, idx)
        return (emotion, eye)

    def __call__(self, time: float) -> Optional[np.ndarray]:
        idx = self.get_state(time)
        if idx < 0:
            return None
        emotion = self.character_timeline[idx]
        character = self.character_imgs[emotion]
        if isinstance(character, Path):
            base_img = np.asarray(PILImage.open(character).convert("RGBA"))
            self.character_imgs[emotion] = base_img
        else:
            base_img = character

        if emotion in self.eye_imgs:
            eye_number = self.get_eye_state(time, idx)
            eye = self.eye_imgs[emotion][eye_number]
            if isinstance(eye, Path):
                eye_img = np.asarray(PILImage.open(eye).convert("RGBA"))
                self.eye_imgs[emotion][eye_number] = eye_img
            else:
                eye_img = eye
            base_img = alpha_composite(base_img, eye_img)
        return base_img
