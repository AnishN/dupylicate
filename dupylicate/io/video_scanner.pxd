from dupylicate.libs.c cimport *
from dupylicate.io.video_reader cimport *
from dupylicate.io.video_matches cimport *

cdef class VideoScanner:
    cdef:
        bint include_images
        bint include_videos
        size_t num_thumbnails
        size_t thumbnail_width
        size_t thumbnail_height
        size_t similarity
        bint seek_exact

        float *positions
        readonly uint8_t[:, :, :, ::1] thumbnails
        readonly bint[::1] included_files
        readonly FileInfo[::1] file_infos
        readonly uint64_t[::1] groups
        size_t num_files
        readonly size_t num_groups
        list files
        public VideoReader reader
    
    cdef float get_percent_diff(self, uint8_t[:, ::1] a, uint8_t[:, ::1] b) nogil
    cdef void save_thumbnail(self, size_t i, size_t j) nogil