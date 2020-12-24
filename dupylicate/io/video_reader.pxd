from dupylicate.libs.c cimport *
from dupylicate.libs.ffmpeg cimport *

ctypedef struct FileInfo:
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

cdef class VideoReader:
    cdef:
        char *file_path
        size_t width
        size_t height
        size_t thumbnail_width
        size_t thumbnail_height
        AVFormatContext *av_format_ctx
        AVCodecContext *av_codec_ctx
        int video_stream_index
        int audio_stream_index
        AVFrame *av_frame_original
        AVFrame *av_frame_thumbnail
        uint8_t *thumbnail_buffer
        AVPacket *av_packet
        SwsContext *sws_scaler_ctx

    cdef bint open(self, char *file_path) nogil
    cdef void get_info(self, FileInfo *info_ptr) nogil
    cdef bint read_thumbnail(self, uint8_t[:, ::1] thumbnail) nogil
    cdef bint seek_exact(self, int64_t time_stamp) nogil
    cdef bint seek_approx(self, int64_t time_stamp) nogil
    cdef void close(self) nogil