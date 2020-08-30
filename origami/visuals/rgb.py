"""Module containing functions that generate RGB plots"""
# Standard library imports
from typing import List
from typing import Tuple
from typing import Union
from typing import Optional
from itertools import cycle

# Third-party imports
import numpy as np
from skimage import exposure
from skimage.color import gray2rgb

# Local imports
from origami.utils.color import convert_hex_to_rgb_1
from origami.utils.utilities import rescale

np.seterr(divide="ignore", invalid="ignore")

COLORS = cycle(
    [
        "#800000",
        "#9A6324",
        "#469990",
        "#000075",
        "#E6194B",
        "#3CB44B",
        "#A9A9A9",
        "#F58231",
        "#FFC119",
        "#3CB44B",
        "#42D4F4",
        "#F032E6",
        "#AAFFC3",
    ]
)


class ImageRGBA:
    """RGBA conversion class"""

    def __init__(self, images: List[np.ndarray], colors: Optional[List] = None):
        """Class to quickly generate composite RGBA images based on ion (or other) images

        This class simplifies generation of composite images by remapping individual ion images to their respective
        colors, which can be quite useful when visualising multiple species at the same time.

        Parameters
        ----------
        images : List[np.ndarray]
            list of flat images
        colors : Optional[List]
            list of colors - if None have been specified, a set of defaults will be used instead
        """
        self.validate(images, colors)

        self._original, self._images, self._colors = self.cleanup(images, colors)
        self._rgba = None

    def __repr__(self):
        return f"ImageRGBA <images={len(self._images)}>"

    @staticmethod
    def _convert_color(color):
        """Convert hex/rgb color"""
        if isinstance(color, str):
            return convert_hex_to_rgb_1(color)
        if isinstance(color, (tuple, list)):
            if np.max(color) > 1.0:
                raise ValueError("RGB(A) colors must be provided in the 0-1 range")
            return color

    @property
    def intensities(self) -> np.ndarray:
        """Return summed intensities from the original data"""
        return np.sum(self._original, axis=0)

    @property
    def rgb(self) -> np.ndarray:
        """Return combined image array without the alpha channel"""
        return self.rgba[:, :, 0:3].astype(np.uint8)

    @property
    def rgba(self) -> np.ndarray:
        """Return combined image array with the alpha channel"""
        if self._rgba is None:
            self._rgba = self.combine().astype(np.uint8)
        return self._rgba

    @rgba.setter
    def rgba(self, array: np.ndarray):
        if array is not None and array.shape[2] != 4:
            raise ValueError("Cannot set RGBA array without the alpha channel")
        self._rgba = array

    @staticmethod
    def validate(images: List[np.ndarray], colors: Optional[List[str]]) -> None:
        """Validate image input

        Parameters
        ----------
        images : List[np.ndarray]
            list of 2D numpy arrays
        colors : Optional[List[str]]
            list of hex colors

        Raises
        ------
        ValueError
            raised if image shapes are not compatible
        """
        if not isinstance(images, list):
            raise ValueError("Expected list of images")

        images = [np.asarray(image) for image in images]
        shapes = set()
        for image in images:
            shapes.add(image.shape)

        if len(shapes) > 1:
            raise ValueError("Images must be of the same size")

        # if color list was specified, make sure the values are correct
        if colors is not None:
            if len(images) != len(colors):
                raise ValueError(
                    f"Please provide the same number of colors as images. Number of images: {len(images)}"
                    f" and colors: {len(colors)}"
                )
            for color in colors:
                if isinstance(color, str):
                    if not color.startswith("#"):
                        raise ValueError("Hex color must start with a hash e.g. `#FF00FF`")
                elif isinstance(color, list):
                    color_len = len(color)
                    if color_len not in [3, 4]:
                        raise ValueError("RGB(A) color must have between 3-4 values (R, G, B and A)")
                    if np.max(color) > 1.0:
                        raise ValueError("RGB(A) color must be between 0-1")
                else:
                    raise ValueError("Color must be a string (hex) or list (RGBA in range 0-1)")

    def reset(self):
        """Reset the store RGBA array to ignore previously made changes (e.g. channel normalizations)"""
        self.rgba = None

    def cleanup(self, images: List[np.ndarray], colors: Optional[List[str]]) -> Tuple[List, List, List]:
        """Clean-up and remap images to appropriate color

        Parameters
        ----------
        images : List[np.ndarray]
            list of 2D numpy arrays
        colors : Optional[List[str]]
            list of hex colors

        Returns
        -------
        images : List
            list of remapped images
        _images : List
            list of original images
        colors : List
            color iterable
        """
        if colors is None:
            colors = [next(COLORS) for _ in images]

        _images = []
        for image, color in zip(images, colors):
            if len(image.shape) == 2:
                image = self._to_rgb(image, self._convert_color(color))
            _images.append(image)

        return images, _images, colors

    @staticmethod
    def _to_rgb(
        image: np.ndarray, color: Union[List, Tuple], add_alpha: bool = True, max_value: Union[int, float] = 255
    ) -> np.ndarray:
        """Convert flat array to multi-channel RGB image based on the specified color

        Parameters
        ----------
        image : np.ndarray
            flat image array
        color : Union[Tuple, List]
            chosen RGB color in the scale 0-255
        add_alpha : bool
            if `True`, 4-th alpha channel will be added to the image array
        max_value : Union[int, float]
            maximum value the image should be rescaled to

        Returns
        -------
        rgb : np.ndarray
            3/4-dimensional image array remapped to the `color`

        """
        image = gray2rgb(rescale(np.nan_to_num(image), 0, max_value), alpha=add_alpha)

        if add_alpha and len(color) == 3:
            color.append(1.0)

        return image * color

    def recolor(self, image_id: int, color: Union[str, List]):
        """Change color of particular image

        Parameters
        ----------
        image_id : int
            index of the image
        color : Union[str, List]
            new color of the image
        """
        if image_id > len(self._images) - 1:
            raise ValueError("Cannot update color of image that is not present")

        self._colors[image_id] = color
        color = self._convert_color(color)
        self._images[image_id] = self._to_rgb(self._original[image_id], color)
        self.reset()

    def get_one(self, image_id: int, keep_alpha: bool = False, dtype=np.uint8, fill_alpha: int = None):
        """Retrieve single 3/4D image

        Parameters
        ----------
        image_id : int
            index of the image
        keep_alpha : bool, optional
            if `True`, the alpha channel will be retained in the image
        dtype :
            data type of the image - matplotlib and Bokeh expect uint8 values to represent images
        fill_alpha : int, optional
            if value is an integer and `keep_alpha` is True, alpha channel will be filled with the specified value

        Returns
        -------
        array : np.ndarray
            3/4D image array mapped to specific color
        """
        if image_id > len(self._images) - 1:
            raise ValueError("Tried to retrieve image that is not present")

        if keep_alpha:
            image = self._images[image_id].astype(dtype)
            if fill_alpha is not None and isinstance(fill_alpha, int):
                image[:, :, 3] = fill_alpha
            return image
        return self._images[image_id][:, :, :3].astype(dtype)

    def get_rgba(self, fill_alpha: int = None):
        """Retrieve RGBA image"""
        image = self.rgba
        if fill_alpha is not None and isinstance(fill_alpha, int):
            image[:, :, 3] = fill_alpha

        return image

    def combine(self, max_value: Union[int, float] = 255, dtype=np.uint8) -> np.ndarray:
        """Combine multiple images into one

        Parameters
        ----------
        max_value : Union[int, float]
            maximum value the image should be rescaled to
        dtype : np.dtype
            numpy data type

        Returns
        -------
        combined_rgb : nd.array
            3/4-dimensional image from multiple images
        """
        return self._combine(self._images, max_value, dtype)

    @staticmethod
    def _combine(images: List[np.ndarray], max_value: Union[int, float], dtype) -> np.ndarray:
        """Combine multiple images into one

        Parameters
        ----------
        images : List[np.ndarray]
            list of RGBA images
        max_value : Union[int, float]
            maximum value the image should be rescaled to
        dtype : np.dtype
            numpy data type

        Returns
        -------
        combined_rgb : nd.array
            3/4-dimensional image from multiple images
        """
        combined_rgb = np.sum(images, axis=0)
        combined_rgb = np.clip(combined_rgb, 0, max_value)
        return combined_rgb.astype(dtype)

    def clip_channel(
        self, channel: int, min_int: Optional[Union[int, float]] = None, max_int: Optional[Union[int, float]] = None
    ):
        """Normalize image channel to increase/decrease intensity

        Parameters
        ----------
        channel : int
            channel to normalize
        min_int : Optional[Union[int, float]]
            scalar value to normalize the minimum of the channel to
        max_int : Optional[Union[int, float]]
            scalar value to normalize the maximum of the channel to

        Returns
        -------
        self : ImageRGBA
            returns self to enable chaining of multiple commands in one go

        Examples
        --------
        Instantiate ImageRGBA and normalize each channel to the same intensity range between 20-200

        >>> np.random.seed(42)
        >>> images = [np.random.randint(0, 255, (3, 3))]
        >>> image_rgba = ImageRGBA(images, colors=["#800000"])
        >>> image_rgba.clip_channel(0, 20, 200).clip_channel(1, 20, 200).clip_channel(2, 20, 200).rgba
        array([[[ 64, 200, 200, 255],
                [120, 200, 200, 255],
                [ 57, 200, 200, 255]],
        <BLANKLINE>
               [[ 20, 200, 200, 255],
                [ 67, 200, 200, 255],
                [ 41, 200, 200, 255]],
        <BLANKLINE>
               [[200, 200, 200, 255],
                [ 20, 200, 200, 255],
                [ 64, 200, 200, 255]]], dtype=uint8)
        """
        # if image is None:
        image = self.rgba
        v_min = image[:, :, channel].min()
        v_max = image[:, :, channel].max()
        self.rgba = self._clip_channel(image, channel, v_min, v_max, min_int, max_int)
        return self

    @staticmethod
    def _clip_channel(
        image: np.ndarray,
        channel: int,
        v_min: Union[int, float],
        v_max: Union[int, float],
        min_value: Union[int, float] = 0,
        max_value: Union[int, float] = 255,
    ):
        """Normalize image channel to increase/decrease intensity

        Parameters
        ----------
        image : np.ndarray
            3/4D image array
        channel : int
            channel to normalize
        v_min : Union[int, float]
            scalar value to normalize the minimum of the channel to
        v_max : Union[int, float]
            scalar value to normalize the maximum of the channel to
        min_value : Union[int, float]
            minimum clipping value
        max_value : Union[int, float]
            maximum clipping value
        Returns
        -------
        image : np.ndarray
            3/4D image with one of the channels normalized to the `v_min`/`v_max` values
        """
        im_channel = image[:, :, channel]
        im_channel[im_channel <= v_min] = min_value
        im_channel[im_channel >= v_max] = max_value
        im_channel = np.clip(im_channel, min_value, max_value)
        image[:, :, channel] = im_channel
        return image

    # noinspection PyTypeChecker
    def quantile_rescale(self, q_low: float = 0.02, q_high: float = 0.98, image: Optional[np.ndarray] = None):
        """Contrast enhancement using stretching or shrinking of intensity levels

        Returns
        -------
        q_low : float
            low boundary quantile
        q_high : float
            high boundary quantile
        image : Optional[np.ndarray]
            image array, if one is not provided, the `rgba` attribute will be used instead

        Returns
        -------
        rgb_image : np.ndarray
            image after rescaling
        """
        if 0 < q_low > 1:
            raise ValueError(f"`q_low` should be between 0 and 1 (not {q_low})")
        if 0 < q_high > 1:
            raise ValueError(f"`q_high` should be between 0 and 1 (not {q_high})")
        if image is None:
            image = self.rgba
        p_low, p_high = np.quantile(image, [q_low, q_high])
        return exposure.rescale_intensity(image, in_range=(p_low, p_high))

    # noinspection PyTypeChecker
    def equalize_histogram(self, n_bins: int = 256, image: Optional[np.ndarray] = None):
        """Contrast enhancement using histogram equalization

        Parameters
        ----------
        n_bins : int, optional
            number of bins for image histogram
        image : Optional[np.ndarray]
            image array, if one is not provided, the `rgba` attribute will be used instead

        Returns
        -------
        rgb_image : np.ndarray
            equalized image
        """
        if image is None:
            image = self.rgba
        return exposure.equalize_hist(image, n_bins)

    def adaptive_histogram(self, clip_limit: float = 0.01, n_bins: int = 256, image: Optional[np.ndarray] = None):
        """Contrast Limited Adaptive Histogram Equalization

        Locally enhance contrast of a RGBA image. The algorithm computes histograms over different tile regions of
        the image.

        Parameters
        ----------
        clip_limit : float, optional
            image clipping limit, normalized between 0 and 1 (higher values give more contrast)
        n_bins : int, optional
            number of gray bins for histogram
        image : Optional[np.ndarray]
            image array, if one is not provided, the `rgba` attribute will be used instead

        Returns
        -------
        rgb_image : np.ndarray
            equalized image
        """
        if image is None:
            image = self.rgba
        return exposure.equalize_adapthist(image, nbins=n_bins, clip_limit=clip_limit)

    def get_colormap(self, image_id: int, n_bins: int = 256, name: str = "colormap"):
        """Create linear colormap

        Parameters
        ----------
        image_id : int
            index of the image/color
        n_bins : int, optional
            number of values in the colormap
        name : str, optional
            name of the colormap

        Returns
        -------
        colormap : ListedColormap
            colormap
        """
        from matplotlib.colors import ListedColormap

        if image_id > len(self._images) - 1:
            raise ValueError("Tried to retrieve image that is not present")

        color = self._convert_color(self._colors[image_id])
        lin_range = np.linspace(0, 1.0, n_bins)
        array = np.zeros((n_bins, len(color)))
        array[:, 0] = lin_range * color[0]
        array[:, 1] = lin_range * color[1]
        array[:, 2] = lin_range * color[2]

        colormap = ListedColormap(array, name)
        return colormap
