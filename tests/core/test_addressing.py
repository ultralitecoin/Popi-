import unittest

from fractal_blockchain.core.addressing import (
    AddressedFractalCoordinate,
    coord_to_string, string_to_coord,
    compress_address, decompress_address # Placeholders
)
from fractal_blockchain.core.mathematics.fractal_math import FractalCoordinate

class TestFractalAddressing(unittest.TestCase):

    def test_addressed_fractal_coordinate_creation(self):
        # Valid solid path
        afc_solid = AddressedFractalCoordinate(depth=2, path=(0, 1))
        self.assertEqual(afc_solid.depth, 2)
        self.assertEqual(afc_solid.path, (0, 1))
        self.assertTrue(afc_solid.is_solid_path())
        self.assertFalse(afc_solid.is_void_path())

        # Valid void path
        afc_void = AddressedFractalCoordinate(depth=3, path=(0, 3, 1))
        self.assertEqual(afc_void.depth, 3)
        self.assertEqual(afc_void.path, (0, 3, 1))
        self.assertFalse(afc_void.is_solid_path())
        self.assertTrue(afc_void.is_void_path())

        # Genesis coordinate
        afc_genesis = AddressedFractalCoordinate(depth=0, path=tuple())
        self.assertEqual(afc_genesis.depth, 0)
        self.assertEqual(afc_genesis.path, tuple())
        self.assertTrue(afc_genesis.is_solid_path()) # No '3' in path
        self.assertFalse(afc_genesis.is_void_path())

        # Invalid path element
        with self.assertRaises(ValueError):
            AddressedFractalCoordinate(depth=1, path=(4,))
        with self.assertRaises(ValueError):
            AddressedFractalCoordinate(depth=1, path=(-1,))

        # Path length mismatch
        with self.assertRaises(ValueError):
            AddressedFractalCoordinate(depth=1, path=(0, 1))
        with self.assertRaises(ValueError):
            AddressedFractalCoordinate(depth=2, path=(0,))

    def test_coord_to_string(self):
        fc_orig = FractalCoordinate(depth=2, path=(0,1)) # Original type
        afc_solid = AddressedFractalCoordinate(depth=2, path=(0, 1))
        afc_void = AddressedFractalCoordinate(depth=3, path=(0, 3, 1))
        afc_genesis = AddressedFractalCoordinate(depth=0, path=tuple())

        self.assertEqual(coord_to_string(fc_orig), "d2p01")
        self.assertEqual(coord_to_string(afc_solid), "d2p01")
        self.assertEqual(coord_to_string(afc_void), "d3p031")
        self.assertEqual(coord_to_string(afc_genesis), "d0p") # Empty path

    def test_string_to_coord(self):
        # Valid conversions (allow_void_paths=True by default)
        self.assertEqual(string_to_coord("d2p01"), AddressedFractalCoordinate(depth=2, path=(0, 1)))
        self.assertEqual(string_to_coord("d3p031"), AddressedFractalCoordinate(depth=3, path=(0, 3, 1)))
        self.assertEqual(string_to_coord("d0p"), AddressedFractalCoordinate(depth=0, path=tuple()))

        # Test with allow_void_paths=False
        # Should return FractalCoordinate type for solid paths
        res_solid_strict = string_to_coord("d2p01", allow_void_paths=False)
        self.assertIsInstance(res_solid_strict, FractalCoordinate) # Check type
        self.assertNotIsInstance(res_solid_strict, AddressedFractalCoordinate) # Check it's not the subclass
        self.assertEqual(res_solid_strict, FractalCoordinate(depth=2, path=(0,1)))

        # Should raise error for void paths if allow_void_paths=False
        with self.assertRaises(ValueError):
            string_to_coord("d3p031", allow_void_paths=False)

        # Test for path elements > 2 when allow_void_paths=False
        with self.assertRaises(ValueError): # string_to_coord will raise ValueError for path element 3
            string_to_coord("d1p3", allow_void_paths=False)


        # Invalid string formats
        self.assertIsNone(string_to_coord("d2p0"))       # Path length doesn't match depth
        self.assertIsNone(string_to_coord("dp01"))        # Missing depth
        self.assertIsNone(string_to_coord("d-1p0"))       # Negative depth
        self.assertIsNone(string_to_coord("d1p012"))      # Path length doesn't match depth
        self.assertIsNone(string_to_coord("d1pA"))        # Invalid char in path
        self.assertIsNone(string_to_coord("d1p0x1"))      # Invalid char in path
        self.assertIsNone(string_to_coord("d2p031_inv"))  # Invalid char in path
        self.assertIsNone(string_to_coord("d1p"))         # Empty path for depth > 0
        self.assertIsNone(string_to_coord("d1"))          # Missing 'p' separator
        self.assertIsNone(string_to_coord("p01"))         # Missing 'd' prefix

        # Path element validation within string_to_coord for AddressedFractalCoordinate
        self.assertIsNone(string_to_coord("d1p4")) # AddressedFractalCoordinate constructor will raise ValueError, caught by string_to_coord
        self.assertIsNone(string_to_coord("d1p-1"))


    def test_compression_placeholders(self):
        # These are just placeholders, so they should effectively use the standard methods
        afc = AddressedFractalCoordinate(depth=2, path=(0, 1))
        compressed_str = compress_address(afc)
        self.assertEqual(compressed_str, coord_to_string(afc))

        decompressed_coord = decompress_address(compressed_str)
        self.assertEqual(decompressed_coord, afc)

        # Test with a void path too
        afc_void = AddressedFractalCoordinate(depth=3, path=(0,3,1))
        compressed_void_str = compress_address(afc_void)
        self.assertEqual(compressed_void_str, coord_to_string(afc_void))

        decompressed_void_coord = decompress_address(compressed_void_str)
        self.assertEqual(decompressed_void_coord, afc_void)

if __name__ == '__main__':
    unittest.main()
