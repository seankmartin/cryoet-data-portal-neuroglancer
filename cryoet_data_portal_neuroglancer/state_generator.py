from pathlib import Path
from typing import Any, Optional

from cryoet_data_portal_neuroglancer.models.json_generator import (
    AnnotationJSONGenerator,
    ImageJSONGenerator,
    ImageVolumeJSONGenerator,
    SegmentationJSONGenerator,
)
from cryoet_data_portal_neuroglancer.utils import get_scale


def _setup_creation(
    source: str,
    name: str = None,
    url: str = None,
    zarr_path: str = None,
    scale: float | tuple[float, float, float] = 1.0,
) -> tuple[str, str, str, str, tuple[float, float, float]]:
    name = Path(source).stem if name is None else name
    url = url if url is not None else ""
    zarr_path = zarr_path if zarr_path is not None else source
    scale = get_scale(scale)
    sep = "/" if url else ""
    source = f"{url}{sep}{source}"
    return source, name, url, zarr_path, scale


def _parse_to_vec3_color(input_color: list[str]) -> str:
    """
    Parse the color from a list of strings to a webgl vec3 of rgb color
    """
    if input_color is None:
        output_color = [255, 255, 255]
    elif len(input_color) == 1:
        if input_color[0][0] == "#":
            color = input_color[0]
            output_color = [int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)]
        else:
            output_color = input_color.copy()
    elif len(input_color) == 3:
        output_color = [int(x) for x in input_color]  # type: ignore
    else:
        raise ValueError(f"input must be a list of 3 values, provided: {input_color} or a Hex color string")
    return ",".join(str(x) for x in output_color)


def _validate_color(color: Optional[str]):
    if len(color) != 7 or color[0] != "#":
        raise ValueError("Color must be a hex string e.g. #FF0000")


def generate_point_layer(
    source: str,
    name: str = None,
    url: str = None,
    color: list[str] = None,
    point_size_multiplier: float = 1.0,
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    is_visible: bool = True,
    is_instance_segmentation: bool = False,
) -> dict[str, Any]:
    source, name, url, _, scale = _setup_creation(source, name, url, scale=scale)
    new_color = _parse_to_vec3_color(color)
    return AnnotationJSONGenerator(
        source=source,
        name=name,
        color=new_color,
        point_size_multiplier=point_size_multiplier,
        scale=scale,
        is_visible=is_visible,
        is_instance_segmentation=is_instance_segmentation,
    ).to_json()


def generate_segmentation_mask_layer(
    source: str,
    name: str = None,
    url: str = None,
    color: str = "#FFFFFF",
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    is_visible: bool = True,
) -> dict[str, Any]:
    source, name, url, _, scale = _setup_creation(source, name, url, scale=scale)
    _validate_color(color)
    return SegmentationJSONGenerator(
        source=source,
        name=name,
        color=color,
        scale=scale,
        is_visible=is_visible,
    ).to_json()


def generate_image_layer(
    source: str,
    scale: tuple[float, float, float],
    size: dict[str, float],
    name: str = None,
    url: str = None,
    start: dict[str, float] = None,
    mean: float = None,
    rms: float = None,
    is_visible: bool = True,
) -> dict[str, Any]:
    source, name, url, _, scale = _setup_creation(source, name, url, scale=scale)
    return ImageJSONGenerator(
        source=source,
        name=name,
        scale=scale,
        size=size,
        start=start,
        mean=mean,
        rms=rms,
        is_visible=is_visible,
    ).to_json()


def generate_image_volume_layer(
    source: str,
    name: str = None,
    url: str = None,
    color: str = "#FFFFFF",
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    is_visible: bool = True,
    rendering_depth: int = 10000,
) -> dict[str, Any]:
    source, name, url, _, scale = _setup_creation(source, name, url, scale=scale)
    _validate_color(color)
    return ImageVolumeJSONGenerator(
        source=source,
        name=name,
        color=color,
        scale=scale,
        is_visible=is_visible,
        rendering_depth=rendering_depth,
    ).to_json()


def combine_json_layers(
    layers: list[dict[str, Any]],
    scale: Optional[tuple[float, float, float] | list[float]],
    units: str = "m",
) -> dict[str, Any]:
    image_layers = [layer for layer in layers if layer["type"] == "image"]
    scale = get_scale(scale)
    combined_json = {
        "dimensions": {dim: [res, units] for dim, res in zip("xyz", scale, strict=False)},
        "crossSectionScale": 1.8,
        "projectionOrientation": [0.173, -0.0126, -0.0015, 0.984],
        "layers": layers,
        "selectedLayer": {
            "visible": True,
            "layer": layers[0]["name"],
        },
        "crossSectionBackgroundColor": "#000000",
        "layout": "4panel",
    }
    if image_layers is not None:
        combined_json["position"] = image_layers[0]["_position"]
        combined_json["crossSectionScale"] = image_layers[0]["_crossSectionScale"]

    return combined_json