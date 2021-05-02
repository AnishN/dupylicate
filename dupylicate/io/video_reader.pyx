cdef class VideoReader:
    
    def __cinit__(self, size_t thumbnail_width, size_t thumbnail_height):
        av_log_set_level(AV_LOG_QUIET)
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height
    
    def __dealloc__(self):
        pass

    cpdef bint open(self, char *file_path) except *:
        cdef:
            size_t i
            AVCodecParameters *av_codec_params
            AVCodec *av_codec
            size_t frame_size
        self.file_path = file_path
        self.av_format_ctx = avformat_alloc_context()
        if self.av_format_ctx == NULL:
            return False
        if avformat_open_input(&self.av_format_ctx, file_path, NULL, NULL) != 0:
            return False
        if avformat_find_stream_info(self.av_format_ctx, NULL) < 0:
            return False
        
        #Extract the audio codec first, then the video one, so that the params are overwritten!
        self.audio_stream_index = -1
        for i in range(self.av_format_ctx.nb_streams):
            av_codec_params = self.av_format_ctx.streams[i].codecpar
            if av_codec_params.codec_type == AVMEDIA_TYPE_AUDIO:
                self.audio_stream_index = i
                break

        self.video_stream_index = -1
        for i in range(self.av_format_ctx.nb_streams):
            av_codec_params = self.av_format_ctx.streams[i].codecpar
            if av_codec_params.codec_type == AVMEDIA_TYPE_VIDEO:
                self.video_stream_index = i
                self.width = av_codec_params.width
                self.height = av_codec_params.height
                break
        if self.video_stream_index == -1:
            return False
        
        av_codec = avcodec_find_decoder(av_codec_params.codec_id)
        self.av_codec_ctx = avcodec_alloc_context3(av_codec)
        if self.av_codec_ctx == NULL:
            return False
        if avcodec_parameters_to_context(self.av_codec_ctx, av_codec_params) < 0:
            return False
        if avcodec_open2(self.av_codec_ctx, av_codec, NULL) < 0:
            return False
        self.av_frame_original = av_frame_alloc()
        if self.av_frame_original == NULL:
            return False
        self.av_frame_thumbnail = av_frame_alloc()
        if self.av_frame_thumbnail == NULL:
            return False
        
        frame_size = av_image_get_buffer_size(
            AV_PIX_FMT_GRAY8, 
            self.thumbnail_width, 
            self.thumbnail_height, 
            32,
        )
        self.thumbnail_buffer = <uint8_t *>calloc(frame_size, sizeof(uint8_t))
        av_image_fill_arrays(
            self.av_frame_thumbnail.data,
            self.av_frame_thumbnail.linesize, 
            self.thumbnail_buffer,
            AV_PIX_FMT_GRAY8, 
            self.thumbnail_width, 
            self.thumbnail_height, 
            32,
        )
        
        self.av_packet = av_packet_alloc()
        if self.av_packet == NULL:
            return False
        
        return True
    
    cdef void get_info(self, FileInfo *info_ptr) nogil:
        cdef:
            FILE *file
            AVStream *av_stream
            AVCodecParameters *av_params
            int64_t duration
            int64_t converted_duration
            AVRational time_base
            AVRational frame_rate

        #set default values for file info
        info_ptr.file_type = FILE_TYPE_INVALID
        info_ptr.duration = 0
        info_ptr.width = 0
        info_ptr.height = 0
        info_ptr.bit_rate = 0
        info_ptr.frame_rate = 0
        info_ptr.sample_rate = 0
        info_ptr.num_channels = 0
        info_ptr.video_codec = AV_CODEC_ID_NONE
        info_ptr.audio_codec = AV_CODEC_ID_NONE

        #get file_size
        file = fopen(self.file_path, b"r")
        fseek(file, 0, SEEK_END)
        info_ptr.file_size = ftell(file)
        fseek(file, 0, SEEK_SET)
        fclose(file)
        
        #get video stream data
        if self.video_stream_index != -1:
            av_stream = self.av_format_ctx.streams[self.video_stream_index]
            av_params = av_stream.codecpar
            info_ptr.width = av_params.width
            info_ptr.height = av_params.height
            info_ptr.bit_rate = av_params.bit_rate
            info_ptr.video_codec = av_params.codec_id

            duration = self.av_format_ctx.duration
            if duration == AV_NOPTS_VALUE:
                duration = 0
            time_base = av_stream.time_base
            converted_duration = duration * time_base.den / AV_TIME_BASE * time_base.num
            if converted_duration == 1:
                duration = 0
            info_ptr.duration = duration
            if info_ptr.duration > 0:
                info_ptr.file_type = FILE_TYPE_VIDEO
            else:
                info_ptr.file_type = FILE_TYPE_IMAGE

            frame_rate = av_stream.avg_frame_rate
            if frame_rate.den != 0:
                info_ptr.frame_rate = float(frame_rate.num) / frame_rate.den
        
            #get audio stream data
            if self.audio_stream_index != -1:
                av_stream = self.av_format_ctx.streams[self.audio_stream_index]
                av_params = av_stream.codecpar
                info_ptr.sample_rate = av_params.sample_rate
                info_ptr.num_channels = av_params.channels
                info_ptr.audio_codec = av_params.codec_id

    cpdef bint read_thumbnail(self, uint8_t[:, ::1] thumbnail) except *:
        cdef:
            int response
            uint8_t *thumbnail_ptr = &thumbnail[0, 0]
            size_t y
            uint8_t *dst
            uint8_t *src
        
        while av_read_frame(self.av_format_ctx, self.av_packet) >= 0:
            if self.av_packet.stream_index != self.video_stream_index:
                av_packet_unref(self.av_packet)
                continue
            response = avcodec_send_packet(self.av_codec_ctx, self.av_packet)
            if response < 0:
                return False
            response = avcodec_receive_frame(self.av_codec_ctx, self.av_frame_original)
            if response == AVERROR(EAGAIN) or response == AVERROR_EOF:
                av_packet_unref(self.av_packet)
                continue
            elif response < 0:
                return False
            av_packet_unref(self.av_packet)
            break

        if self.av_codec_ctx.pix_fmt == AV_PIX_FMT_NONE:
            return False
        
        self.sws_scaler_ctx = sws_getContext(
            self.width, self.height, self.av_codec_ctx.pix_fmt,
            self.thumbnail_width, self.thumbnail_height, AV_PIX_FMT_GRAY8,
            SWS_BILINEAR, NULL, NULL, NULL,
        )
        if self.sws_scaler_ctx == NULL:
            return False
        
        sws_scale(
            self.sws_scaler_ctx, 
            self.av_frame_original.data, 
            self.av_frame_original.linesize, 
            0, 
            self.av_frame_original.height, 
            self.av_frame_thumbnail.data,
            self.av_frame_thumbnail.linesize,
        )

        for y in range(self.thumbnail_height):
            dst = thumbnail_ptr + y * (self.thumbnail_width * sizeof(uint8_t))
            src = self.av_frame_thumbnail.data[0] + y * self.av_frame_thumbnail.linesize[0]
            memcpy(dst, src, self.thumbnail_width * sizeof(uint8_t))
        
        sws_freeContext(self.sws_scaler_ctx)
        return True

    cpdef bint read_frame(self, size_t width, size_t height, uint8_t[::1] frame) except *:
        cdef:
            int response
            uint8_t *frame_ptr = &frame[0]
            size_t y
            uint8_t *dst
            uint8_t *src
            size_t bytes_per_line
            AVFrame *av_frame
            size_t frame_size
        
        bytes_per_line = width * 3 * sizeof(uint8_t)
        av_frame = av_frame_alloc()
        if av_frame == NULL:
            return False
        
        frame_size = av_image_get_buffer_size(
            AV_PIX_FMT_RGB24, 
            width,
            height,
            32,
        )
        frame_buffer = <uint8_t *>calloc(frame_size, sizeof(uint8_t))
        av_image_fill_arrays(
            av_frame.data,
            av_frame.linesize, 
            frame_ptr,
            AV_PIX_FMT_RGB24, 
            width,
            height,
            32,
        )

        while av_read_frame(self.av_format_ctx, self.av_packet) >= 0:
            if self.av_packet.stream_index != self.video_stream_index:
                av_packet_unref(self.av_packet)
                continue
            response = avcodec_send_packet(self.av_codec_ctx, self.av_packet)
            if response < 0:
                return False
            response = avcodec_receive_frame(self.av_codec_ctx, self.av_frame_original)
            if response == AVERROR(EAGAIN) or response == AVERROR_EOF:
                av_packet_unref(self.av_packet)
                continue
            elif response < 0:
                return False
            av_packet_unref(self.av_packet)
            break

        if self.av_codec_ctx.pix_fmt == AV_PIX_FMT_NONE:
            return False
        
        self.sws_scaler_ctx = sws_getContext(
            self.width, self.height, self.av_codec_ctx.pix_fmt,
            width, height, AV_PIX_FMT_RGB24,
            SWS_BILINEAR, NULL, NULL, NULL,
        )
        if self.sws_scaler_ctx == NULL:
            return False
        
        sws_scale(
            self.sws_scaler_ctx, 
            self.av_frame_original.data, 
            self.av_frame_original.linesize, 
            0, 
            self.av_frame_original.height, 
            av_frame.data,
            av_frame.linesize,
        )

        for y in range(height):
            dst = frame_ptr + y * bytes_per_line
            src = av_frame.data[0] + y * av_frame.linesize[0]# * 3
            memcpy(dst, src, bytes_per_line)
        
        sws_freeContext(self.sws_scaler_ctx)
        return True

    cpdef bint seek_exact(self, int64_t time_stamp) except *:
        cdef:
            int response
            int i = 0
            int64_t current_time_stamp = 0
            AVStream *av_stream
            AVRational time_base
            int64_t stream_time_stamp
        
        av_stream = self.av_format_ctx.streams[self.video_stream_index]
        time_base = av_stream.time_base
        stream_time_stamp = (time_stamp * time_base.den) / (time_base.num * AV_TIME_BASE)
        av_seek_frame(self.av_format_ctx, self.video_stream_index, stream_time_stamp, AVSEEK_FLAG_BACKWARD)
        while True:
            while av_read_frame(self.av_format_ctx, self.av_packet) >= 0:
                if self.av_packet.stream_index != self.video_stream_index:
                    av_packet_unref(self.av_packet)
                    continue
                response = avcodec_send_packet(self.av_codec_ctx, self.av_packet)
                if response < 0:
                    return False
                response = avcodec_receive_frame(self.av_codec_ctx, self.av_frame_original)
                if response == AVERROR(EAGAIN) or response == AVERROR_EOF:
                    av_packet_unref(self.av_packet)
                    continue
                elif response < 0:
                    return False
                current_time_stamp = self.av_packet.pts
                av_packet_unref(self.av_packet)
                break
            if stream_time_stamp <= current_time_stamp:
                break
        return True

    cpdef bint seek_approx(self, int64_t time_stamp) except *:
        cdef:
            int response
            AVStream *av_stream
            AVRational time_base
            int64_t stream_time_stamp
        
        av_stream = self.av_format_ctx.streams[self.video_stream_index]
        time_base = av_stream.time_base
        stream_time_stamp = (time_stamp * time_base.den) / (time_base.num * AV_TIME_BASE)
        av_seek_frame(self.av_format_ctx, self.video_stream_index, stream_time_stamp, AVSEEK_FLAG_BACKWARD)
        while av_read_frame(self.av_format_ctx, self.av_packet) >= 0:
            if self.av_packet.stream_index != self.video_stream_index:
                av_packet_unref(self.av_packet)
                continue
            response = avcodec_send_packet(self.av_codec_ctx, self.av_packet)
            if response < 0:
                return False
            response = avcodec_receive_frame(self.av_codec_ctx, self.av_frame_original)
            if response == AVERROR(EAGAIN) or response == AVERROR_EOF:
                av_packet_unref(self.av_packet)
                continue
            elif response < 0:
                return False
            av_packet_unref(self.av_packet)
            break
        return True

    cpdef void close(self) except *:
        if self.av_format_ctx != NULL:
            avformat_close_input(&self.av_format_ctx)
            avformat_free_context(self.av_format_ctx)
            self.av_format_ctx = NULL
        if self.av_frame_original != NULL:
            av_frame_free(&self.av_frame_original)
            self.av_frame_original = NULL
        if self.av_frame_thumbnail != NULL:
            av_frame_free(&self.av_frame_thumbnail)
            self.av_frame_thumbnail = NULL
        if self.thumbnail_buffer != NULL:
            free(self.thumbnail_buffer)
            self.thumbnail_buffer = NULL
        if self.av_packet != NULL:
            av_packet_free(&self.av_packet)
            self.av_packet = NULL
        if self.av_codec_ctx != NULL:
            avcodec_free_context(&self.av_codec_ctx)
            self.av_codec_ctx = NULL
        self.video_stream_index = -1
        self.audio_stream_index = -1
        self.file_path = NULL