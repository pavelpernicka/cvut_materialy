/*
 * File name: exam_utils.h
 * Date:      2017/01/16 17:00
 * Author:    Jan Faigl
 */

#ifndef __EXAM_UTILS_H__
#define __EXAM_UTILS_H__

void my_assert(int r, const char *fcname, int line, const char *fname);

void save_ppm_image_red(int w, int h, const char *fname);

void save_ppm_image_green(int w, int h, const char *fname);

void save_binary(int w, int h, int threshold, int* grid, const char *fname);

/*
 * save img as PPM file to fname
 * img is the whole image as a sequence of the RGB values
 */
void save_ppm_image(int w, int h, const unsigned char *img, const char *fname);

#endif

/* end of exam_utils.h */
