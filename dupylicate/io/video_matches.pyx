cdef class VideoMatches:

    def __cinit__(self, size_t num_match_groups, size_t num_match_files):
        cdef:
            Match *data_ptr

        data_ptr = <Match *>calloc(num_match_files, sizeof(Match))
        if data_ptr == NULL:
            raise MemoryError("VideoMatches: unable to allocate matches")
        self.data = <Match[:num_match_files]>data_ptr
        self.num_match_groups = num_match_groups
        self.num_match_files = num_match_files

    def __dealloc__(self):
        free(&self.data[0])
        self.data = None
        self.num_match_groups = 0
        self.num_match_files = 0

    def get_codec_str(self, AVCodecID codec_id):
        cdef:
            bytes codec_bytes
        codec_bytes = avcodec_get_name(codec_id)
        return codec_bytes.decode()