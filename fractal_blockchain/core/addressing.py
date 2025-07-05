# Fractal Coordinate Addressing System

from typing import Tuple, Optional, Union
from fractal_blockchain.core.mathematics.fractal_math import FractalCoordinate

# Prompt 2: Design fractal coordinate addressing system
# - Each position uses a base-4 identifier: sequence of digits (0,1,2 for vertex/child triangle, 3 for void)
#   showing the path from Genesis.
# - Coordinate includes: depth, parent (implicitly by path), and child index (last element of path).
#
# Note: The existing `FractalCoordinate` in `fractal_math.py` already uses a path of integers.
# The prompt specifies base-4 (0,1,2 for children, 3 for void).
# `fractal_math.py` currently only models the solid triangles (children 0,1,2).
# We need to extend this to explicitly include voids in the addressing scheme if '3' is for void.

class AddressedFractalCoordinate(FractalCoordinate):
    """
    Extends FractalCoordinate to potentially include void paths.
    The 'path' tuple can now contain '3' to indicate a path through a void.
    """
    # FractalCoordinate already has:
    # depth: int
    # path: Tuple[int, ...]

    def __new__(cls, depth: int, path: Tuple[int, ...]):
        # Basic validation for path elements if we enforce 0,1,2,3
        for p_el in path:
            if not (0 <= p_el <= 3):
                raise ValueError("Path elements must be 0, 1, 2 (child) or 3 (void).")
        if len(path) != depth:
            raise ValueError("Path length must equal depth.")

        # Use super() to call NamedTuple's __new__ method
        # self = super().__new__(cls, depth, path)
        # For NamedTuple, it's better to just let it be created if structure is same
        instance = super(AddressedFractalCoordinate, cls).__new__(cls, depth, path)
        return instance

    def is_void_path(self) -> bool:
        """Checks if any part of the path goes through a void (digit 3)."""
        return 3 in self.path

    def is_solid_path(self) -> bool:
        """Checks if the path refers to a solid triangle (only digits 0, 1, 2)."""
        return not self.is_void_path()

# --- Address Encoding/Decoding ---

def coord_to_string(coord: Union[FractalCoordinate, AddressedFractalCoordinate]) -> str:
    """
    Encodes a FractalCoordinate or AddressedFractalCoordinate to a string.
    Format: "d<depth>p<path_elements_joined>"
    Example: FractalCoordinate(depth=2, path=(0,1)) -> "d2p01"
             AddressedFractalCoordinate(depth=3, path=(0,3,1)) -> "d3p031"
    """
    path_str = "".join(map(str, coord.path))
    return f"d{coord.depth}p{path_str}"

def string_to_coord(s: str, allow_void_paths: bool = True) -> Optional[Union[FractalCoordinate, AddressedFractalCoordinate]]:
    """
    Decodes a string representation back to a FractalCoordinate or AddressedFractalCoordinate.
    Returns None if the string format is invalid.
    """
    if not s.startswith("d") or "p" not in s:
        return None

    depth_val: int
    path_val: Tuple[int, ...]

    try:
        parts = s.split("p")
        depth_str = parts[0][1:]
        path_str = parts[1]

        depth_val = int(depth_str) # Can raise ValueError
        if depth_val < 0:
            return None

        if not path_str and depth_val == 0:
            path_val = tuple()
        elif not path_str and depth_val > 0: # Path string is empty but depth > 0
             return None
        else:
            path_val = tuple(map(int, list(path_str))) # Can raise ValueError

        if len(path_val) != depth_val:
            return None # Path length must match depth

    except (ValueError, IndexError): # Catch parsing/conversion errors from above block
        return None

    # Now, path_val and depth_val are parsed. Apply logic based on allow_void_paths.
    if allow_void_paths:
        try:
            # AddressedFractalCoordinate constructor validates path elements (0-3)
            return AddressedFractalCoordinate(depth=depth_val, path=path_val)
        except ValueError:
            # This ValueError is from AddressedFractalCoordinate's own validation
            # (e.g. path element '4' which is numerically valid for int() but not for AFC path)
            return None
    else:
        # allow_void_paths is False.
        # Original FractalCoordinate implies solid paths (elements 0-2).
        # We need to ensure no '3's (or other non-solid elements like '4', '-1' if they somehow passed initial int conversion) are in path.
        for p_el in path_val:
            if not (0 <= p_el <= 2):
                # This ValueError should propagate to the caller as per the test's expectation
                # for cases like "d1p3" with allow_void_paths=False.
                raise ValueError("Path contains non-solid elements (e.g. 3 for void, or >3) when allow_void_paths is False.")
        # If all path elements are valid (0-2), construct the basic FractalCoordinate
        return FractalCoordinate(depth=depth_val, path=path_val)


# --- Collision Detection ---
# Uniqueness is inherent in the (depth, path) definition.
# If (depth1, path1) == (depth2, path2), they are the same coordinate.
# Collision detection is more about ensuring canonical forms if multiple string representations
# could map to the same coordinate (which they can't with the current string format).
# So, this is mostly covered by the representation itself.

# --- Address Compression ---
# Placeholder for now. Run-length encoding or other schemes could be complex.
# E.g., path (0,0,0,1,1,2) -> "0*3,1*2,2*1" (string compression)
# Or binary packing.
# For Phase 1, a clear, uncompressed representation is prioritized.

def compress_address(coord: AddressedFractalCoordinate) -> str:
    """
    Placeholder for address compression.
    For now, returns the standard string representation.
    """
    # TODO: Implement actual compression (e.g., run-length encoding for path)
    return coord_to_string(coord)

def decompress_address(compressed_s: str) -> Optional[AddressedFractalCoordinate]:
    """
    Placeholder for address decompression.
    For now, assumes standard string representation.
    """
    # TODO: Implement actual decompression
    return string_to_coord(compressed_s, allow_void_paths=True)


if __name__ == '__main__':
    fc_solid = FractalCoordinate(depth=2, path=(0,1)) # From fractal_math
    afc_solid = AddressedFractalCoordinate(depth=2, path=(0,1))
    afc_void = AddressedFractalCoordinate(depth=3, path=(0,3,1)) # Contains a void step

    print(f"FractalCoordinate (solid): {fc_solid}")
    print(f"AddressedFractalCoordinate (solid): {afc_solid}")
    print(f"AddressedFractalCoordinate (void path): {afc_void}")
    print(f"  Is void path? {afc_void.is_void_path()}")
    print(f"  Is solid path? {afc_void.is_solid_path()}")
    print(f"  Is solid path (afc_solid)? {afc_solid.is_solid_path()}")

    # String encoding/decoding
    s_fc_solid = coord_to_string(fc_solid)
    s_afc_solid = coord_to_string(afc_solid)
    s_afc_void = coord_to_string(afc_void)
    print(f"\nString encodings:")
    print(f"  {fc_solid} -> {s_fc_solid}")
    print(f"  {afc_solid} -> {s_afc_solid}")
    print(f"  {afc_void} -> {s_afc_void}")

    print(f"\nString decodings (allowing voids):")
    decoded_s_fc_solid = string_to_coord(s_fc_solid)
    decoded_s_afc_solid = string_to_coord(s_afc_solid)
    decoded_s_afc_void = string_to_coord(s_afc_void)
    print(f"  {s_fc_solid} -> {decoded_s_fc_solid} (type: {type(decoded_s_fc_solid)})")
    print(f"  {s_afc_solid} -> {decoded_s_afc_solid} (type: {type(decoded_s_afc_solid)})")
    print(f"  {s_afc_void} -> {decoded_s_afc_void} (type: {type(decoded_s_afc_void)})")

    assert decoded_s_afc_solid == afc_solid
    assert decoded_s_afc_void == afc_void

    print(f"\nString decodings (not allowing voids for original FractalCoordinate type):")
    try:
        decoded_s_fc_solid_strict = string_to_coord(s_fc_solid, allow_void_paths=False)
        print(f"  {s_fc_solid} (strict) -> {decoded_s_fc_solid_strict} (type: {type(decoded_s_fc_solid_strict)})")
        assert decoded_s_fc_solid_strict == fc_solid # fc_solid is FractalCoordinate type
    except ValueError as e:
        print(f"  Error decoding {s_fc_solid} strictly: {e}")

    try:
        decoded_s_afc_void_strict = string_to_coord(s_afc_void, allow_void_paths=False)
        print(f"  {s_afc_void} (strict) -> {decoded_s_afc_void_strict}")
    except ValueError as e:
        print(f"  Error decoding {s_afc_void} strictly (expected): {e}")

    # Test invalid strings
    print(f"\nTesting invalid strings:")
    invalid_strs = ["d2p0", "dp01", "d-1p0", "d1p012", "d1pA", "d1p0x1", "d2p031_invalid_char"]
    for inv_s in invalid_strs:
        res = string_to_coord(inv_s)
        print(f"  '{inv_s}' -> {res}")
        assert res is None

    # Test invalid path elements for AddressedFractalCoordinate construction
    try:
        AddressedFractalCoordinate(depth=1, path=(4,))
    except ValueError as e:
        print(f"  Correctly caught error for invalid path element: {e}")

    # Test path length mismatch
    try:
        AddressedFractalCoordinate(depth=1, path=(0,1))
    except ValueError as e:
        print(f"  Correctly caught error for path length mismatch: {e}")

    print("\nBasic addressing functionality seems to be in place.")
    print("Compression/decompression are placeholders.")

    # Genesis coord
    genesis_afc = AddressedFractalCoordinate(depth=0, path=())
    s_genesis = coord_to_string(genesis_afc)
    print(f"Genesis AFC: {genesis_afc} -> {s_genesis}")
    decoded_genesis = string_to_coord(s_genesis)
    print(f"Decoded Genesis: {s_genesis} -> {decoded_genesis}")
    assert decoded_genesis == genesis_afc

    empty_path_str_d0 = "d0p"
    decoded_empty_path_d0 = string_to_coord(empty_path_str_d0)
    print(f"'{empty_path_str_d0}' -> {decoded_empty_path_d0}")
    assert decoded_empty_path_d0 == AddressedFractalCoordinate(0, tuple())

    empty_path_str_d1 = "d1p" # Invalid, path must exist if depth > 0
    decoded_empty_path_d1 = string_to_coord(empty_path_str_d1)
    print(f"'{empty_path_str_d1}' -> {decoded_empty_path_d1}")
    assert decoded_empty_path_d1 is None

    # Test AddressedFractalCoordinate can be used where FractalCoordinate is expected if path is solid
    # This relies on AddressedFractalCoordinate being a structural subtype / duck-typing if not inheritance
    # Since it inherits, it should be fine.
    from fractal_blockchain.core.mathematics.fractal_math import get_children
    children_of_afc_solid = get_children(afc_solid) # afc_solid is AddressedFractalCoordinate(depth=2, path=(0,1))
    print(f"Children of AddressedFractalCoordinate {afc_solid}: {children_of_afc_solid}")
    # Expect children to be FractalCoordinate type as per get_children's annotation
    # but they will be constructed as FractalCoordinate(depth=3, path=(0,1,X))
    self_type_children = [AddressedFractalCoordinate(depth=c.depth, path=c.path) for c in children_of_afc_solid]
    print(f"Children cast to AddressedFractalCoordinate: {self_type_children}")
    assert len(children_of_afc_solid) == 3

    # However, functions in fractal_math currently assume paths are 0,1,2.
    # If we pass afc_void to get_children, it will try to append 0,1,2 to (0,3,1)
    # which is fine for AddressedFractalCoordinate path definition.
    # children_of_afc_void = get_children(afc_void)
    # print(f"Children of AddressedFractalCoordinate {afc_void}: {children_of_afc_void}")
    # This shows that `fractal_math` functions need to be aware of `AddressedFractalCoordinate`
    # or `AddressedFractalCoordinate` needs to override methods like `get_children` if its
    # interpretation of children differs (e.g., a void cannot have children in the same way).
    # For now, the addressing system is about naming. Geometric interpretation is separate.

    print("Prompt 2 initial implementation done.")
