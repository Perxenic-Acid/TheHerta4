import unittest

from utils.srmi_limits import (
    D3D11_MAX_BUFFER_BYTES,
    D3D11_MAX_DISPATCH_GROUPS_PER_DIMENSION,
    SRMI_SKINNING_THREADS_PER_GROUP,
    get_srmi_gpu_vertex_limit,
    validate_srmi_gpu_vertex_count,
)


class SRMIVertexLimitTests(unittest.TestCase):
    def test_limit_respects_d3d11_dispatch_group_count(self):
        expected = D3D11_MAX_DISPATCH_GROUPS_PER_DIMENSION * SRMI_SKINNING_THREADS_PER_GROUP
        self.assertEqual(get_srmi_gpu_vertex_limit(12), expected)
        validate_srmi_gpu_vertex_count(expected, 12, "12345678")

    def test_limit_respects_d3d11_buffer_byte_width(self):
        expected = D3D11_MAX_BUFFER_BYTES // 40
        self.assertEqual(get_srmi_gpu_vertex_limit(40), expected)
        validate_srmi_gpu_vertex_count(expected, 40, "12345678")

    def test_rejects_count_above_safe_limit(self):
        limit = get_srmi_gpu_vertex_limit(40)
        with self.assertRaisesRegex(ValueError, r"12345678.*exceeding the safe limit"):
            validate_srmi_gpu_vertex_count(limit + 1, 40, "12345678")

    def test_rejects_invalid_position_stride(self):
        with self.assertRaisesRegex(ValueError, "Position stride must be positive"):
            get_srmi_gpu_vertex_limit(0)


if __name__ == "__main__":
    unittest.main()
