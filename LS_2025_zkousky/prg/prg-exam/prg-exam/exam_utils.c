/*
 * File name: exam_utils.c
 * Date:      2017/01/16 08:43
 * Author:    Jan Faigl
 */

#include <stdio.h>
#include <stdlib.h>

#include "exam_utils.h"

#define IMAGE_COMMENT "#PRP-exam"

#define MAX_COLOR_VALUE 255

// - function ----------------------------------------------------------------
void my_assert(int r, const char *fcname, int line, const char *fname)
{
   if (!(r)) {
      fprintf(stderr, "ERROR: my_assert FAIL: %s() line %d in %s\n", fcname, line, fname);
      exit(-1);
   }
}

// - function ----------------------------------------------------------------
void save_ppm_image_red(int w, int h, const char *fname)
{
   FILE *fd = fopen(fname, "wb");
   my_assert(fd != NULL, __func__, __LINE__, __FILE__);
   fprintf(fd, "P6\n %s\n %d\n %d\n %d\n", IMAGE_COMMENT, w, h, MAX_COLOR_VALUE);
   unsigned char color[3] = {255, 0, 0}; /* R G B */
   for (int y = 0; y < h; ++y) {
      for (int x = 0; x < w; ++x) {
         my_assert(fwrite(color, 1, 3, fd) == 3, __func__, __LINE__, __FILE__);
      }
   }
   fclose(fd);
}

// - function ----------------------------------------------------------------
void save_ppm_image_green(int w, int h, const char *fname)
{
   FILE *fd = fopen(fname, "wb");
   my_assert(fd != NULL, __func__, __LINE__, __FILE__);
   fprintf(fd, "P6\n %s\n %d\n %d\n %d\n", IMAGE_COMMENT, w, h, MAX_COLOR_VALUE);
   unsigned char color[3] = {0, 255, 0}; /* R G B */
   for (int y = 0; y < h; ++y) {
      for (int x = 0; x < w; ++x) {
         my_assert(fwrite(color, 1, 3, fd) == 3, __func__, __LINE__, __FILE__);
      }
   }
   fclose(fd);
}

/* end of exam_utils.c */
