"""SRMI GPU pre-skinning limits imposed by its compute path and D3D11."""

D3D11_MAX_BUFFER_BYTES = 128 * 1024 * 1024
D3D11_MAX_DISPATCH_GROUPS_PER_DIMENSION = 65535
SRMI_SKINNING_THREADS_PER_GROUP = 64


def get_srmi_gpu_vertex_limit(position_stride: int) -> int:
    if position_stride <= 0:
        raise ValueError(f"SRMI Position stride must be positive, got {position_stride}")

    # SRMI's skinning shaders use 64 threads per group, and D3D11 caps each
    # Dispatch dimension at 65,535 groups.
    dispatch_vertex_limit = (
        D3D11_MAX_DISPATCH_GROUPS_PER_DIMENSION
        * SRMI_SKINNING_THREADS_PER_GROUP
    )
    # The generated VertexLimitRaise resizes the Position buffer by stride * count.
    buffer_vertex_limit = D3D11_MAX_BUFFER_BYTES // position_stride
    return min(dispatch_vertex_limit, buffer_vertex_limit)


def validate_srmi_gpu_vertex_count(vertex_count: int, position_stride: int, draw_ib: str) -> None:
    limit = get_srmi_gpu_vertex_limit(position_stride)
    if vertex_count > limit:
        raise ValueError(
            f"SRMI GPU-PreSkinning DrawIB {draw_ib} has {vertex_count:,} vertices, "
            f"exceeding the safe limit of {limit:,} for Position stride {position_stride}. "
            "Reduce the mesh vertex count or export pieces under distinct DrawIB targets."
        )
