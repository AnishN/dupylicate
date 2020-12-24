import os
import time

cdef class VideoScanner:
    def __cinit__(self, 
            bint include_images, bint include_videos,
            size_t num_thumbnails, size_t thumbnail_width, size_t thumbnail_height,
            size_t similarity, bint seek_exact):
        cdef:
            size_t i

        self.include_images = include_images
        self.include_videos = include_videos
        self.num_thumbnails = num_thumbnails
        self.positions = <float *>calloc(self.num_thumbnails, sizeof(float))
        for i in range(self.num_thumbnails):
            self.positions[i] = <float>(i + 1) / (self.num_thumbnails + 1)
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height
        self.similarity = similarity
        self.seek_exact = seek_exact
        self.reader = VideoReader(self.thumbnail_width, self.thumbnail_height)

    def __dealloc__(self):
        pass
    
    def startup(self, list files):
        cdef:
            size_t width = self.thumbnail_width
            size_t height = self.thumbnail_height
            size_t num_items
            void *thumbnails_ptr
            void *included_files_ptr
            void *file_infos_ptr
            void *groups_ptr
        
        self.files = files
        self.num_files = len(files)

        num_items = self.num_files * self.num_thumbnails * height * width
        data_ptr = calloc(num_items, sizeof(uint8_t))
        if data_ptr == NULL:
            raise MemoryError("Unable to allocate memory for thumbnails")
        self.thumbnails = <uint8_t[:self.num_files, :self.num_thumbnails, :height, :width]>data_ptr

        num_items = self.num_files
        included_ptr = calloc(num_items, sizeof(bint))
        if included_ptr == NULL:
            raise MemoryError("Unable to allocate memory for included files list")
        self.included_files = <bint[:self.num_files]>included_ptr
        
        num_items = self.num_files
        file_infos_ptr = calloc(num_items, sizeof(FileInfo))
        if file_infos_ptr == NULL:
            raise MemoryError("Unable to allocate memory for file infos")
        self.file_infos = <FileInfo[:self.num_files]>file_infos_ptr

        num_items = self.num_files
        data_ptr = calloc(num_items, sizeof(uint64_t))
        if data_ptr == NULL:
            raise MemoryError("Unable to allocate memory for groups")
        self.groups = <uint64_t[:self.num_files]>data_ptr
        self.num_groups = 0

    def cleanup(self):
        free(&self.thumbnails[0, 0, 0, 0]); self.thumbnails = None
        free(&self.included_files[0]); self.included_files = None
        free(&self.file_infos[0]); self.file_infos = None
        free(&self.groups[0]); self.groups = None
        self.files = None
        self.num_files = 0

    def extract_file_thumbnails(self, size_t i):
        cdef:
            size_t j
            bytes file_path
            bint success
            uint8_t[:, ::1] thumbnail
            int64_t duration
            int64_t thumbnail_time_stamp
            bint included = False
            bint is_image
            bint is_video
            FileInfo *info_ptr
        
        file_path = self.files[i]
        info_ptr = &self.file_infos[i]
        success = self.reader.open(file_path)
        if success:
            with nogil:
                self.reader.get_info(info_ptr)
                duration = info_ptr.duration
                is_video = duration > 0
                included = (not is_video and self.include_images) or (is_video and self.include_videos)
                if included:
                    #print(i, file_path, is_video, duration)
                    if is_video:
                        for j in range(self.num_thumbnails):
                            thumbnail_time_stamp = <int64_t>(self.positions[j] * duration)
                            #print(j, thumbnail_time_stamp)
                            if self.seek_exact:
                                success = self.reader.seek_exact(thumbnail_time_stamp)
                            else:
                                success = self.reader.seek_approx(thumbnail_time_stamp)
                            #print(success)
                            if success:
                                self.reader.read_thumbnail(self.thumbnails[i, j])
                                #self.save_thumbnail(i, j)
                            else:
                                included = False
                                #break
                    else:#must be image
                        for j in range(self.num_thumbnails):
                            self.reader.read_thumbnail(self.thumbnails[i, j])
                            #self.save_thumbnail(i, j)
        #print(i, file_path, duration, included, self.include_images, self.include_videos)
        self.included_files[i] = included
        self.reader.close()

    cdef void save_thumbnail(self, size_t i, size_t j) nogil:
        cdef:
            uint8_t[:, ::1] thumbnail = self.thumbnails[i, j]
            FILE *file_ptr
            char szFilename[32]
            size_t height = thumbnail.shape[0]
            size_t width = thumbnail.shape[1]
        
        sprintf(szFilename, "file_%d_%d.ppm", i, j)
        file_ptr = fopen(szFilename, "wb")
        if file_ptr == NULL:
            return
        fprintf(file_ptr, "P5\n%d %d\n255\n", width, height)
        fwrite(&thumbnail[0, 0], sizeof(uint8_t), height * width, file_ptr)
        fclose(file_ptr)

    def determine_file_group(self, size_t i):
        cdef:
            size_t j, k
            uint8_t[:, ::1] thumbnail_a
            uint8_t[:, ::1] thumbnail_b
            float diff, diff_sum, diff_avg
            float threshold = 1.0 - (self.similarity / 100.0)
        if self.included_files[i]:
            for j in range(i):
                if self.included_files[j]:
                    diff_sum = 0.0
                    for k in range(self.num_thumbnails):
                        thumbnail_a = self.thumbnails[i, k]
                        thumbnail_b = self.thumbnails[j, k]
                        diff = self.get_percent_diff(thumbnail_a, thumbnail_b)
                        diff_sum += diff
                    diff_avg = diff_sum / self.num_thumbnails
                    if diff_avg < threshold:
                        if self.groups[j] == 0:
                            self.num_groups += 1
                            self.groups[i] = self.num_groups
                            self.groups[j] = self.num_groups
                        else:
                            self.groups[i] = self.groups[j]
    
    def get_matches(self):
        cdef:
            VideoMatches matches
            size_t num_match_groups = 0
            size_t num_match_files = 0
            size_t i, j, k
            Match *match_ptr
            FileInfo *info_ptr
            bytes file_path
            size_t file_path_len

        num_match_groups = self.num_groups
        for i in range(self.num_files):
            if self.groups[i] != 0:
                num_match_files += 1

        if num_match_files == 0:
            matches = None
        else:
            matches = VideoMatches(num_match_groups, num_match_files)
            k = 0
            for i in range(self.num_groups):
                for j in range(self.num_files):
                    if self.groups[j] == i + 1:
                        match_ptr = &matches.data[k]
                        
                        match_ptr.group_num = i
                        match_ptr.file_num = j
                        file_path = self.files[j]
                        file_path_len = len(file_path)
                        if file_path_len > 4096:
                            raise ValueError("VideoScanner: file path length > 4096 characters")
                        memcpy(&match_ptr.file_path[0], <char *>file_path, file_path_len)
                        info_ptr = &self.file_infos[j]
                        match_ptr.file_size = info_ptr.file_size
                        match_ptr.duration = info_ptr.duration
                        match_ptr.width = info_ptr.width
                        match_ptr.height = info_ptr.height
                        match_ptr.bit_rate = info_ptr.bit_rate
                        match_ptr.frame_rate = info_ptr.frame_rate
                        match_ptr.sample_rate = info_ptr.sample_rate
                        match_ptr.num_channels = info_ptr.num_channels
                        match_ptr.video_codec = info_ptr.video_codec
                        match_ptr.audio_codec = info_ptr.audio_codec
                        k += 1
        return matches

    cdef float get_percent_diff(self, uint8_t[:, ::1] a, uint8_t[:, ::1] b) nogil:
        cdef:
            size_t r, c
            uint64_t diff = 0
            float percent_diff
        if a.shape[0] != b.shape[0] or a.shape[1] != b.shape[1]:
            return 1.0
        for r in range(a.shape[0]):
            for c in range(a.shape[1]):
                diff += c_abs(a[r, c] - b[r, c])
        return <float>diff / (255 * a.shape[0] * a.shape[1])