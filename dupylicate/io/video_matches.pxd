from dupylicate.libs.c cimport *
from dupylicate.libs.ffmpeg cimport *

ctypedef struct Match:
    size_t group_num
    size_t file_num
    char[4096] file_path
    uint8_t file_type
    size_t file_size
    int64_t duration
    int width
    int height
    int64_t bit_rate
    float frame_rate
    int sample_rate
    int num_channels
    uint64_t video_codec
    uint64_t audio_codec

cdef class VideoMatches:
    cdef:
        readonly Match[::1] data
        readonly size_t num_match_groups
        readonly size_t num_match_files