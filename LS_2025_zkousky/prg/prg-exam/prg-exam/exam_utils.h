/*
 * File name: exam_utils.h
 * Date:      2017/01/16 08:43
 * Author:    Jan Faigl
 */

#ifndef __EXAM_UTILS_H__
#define __EXAM_UTILS_H__

void my_assert(int r, const char *fcname, int line, const char *fname);

void save_ppm_image_red(int w, int h, const char *fname);

void save_ppm_image_green(int w, int h, const char *fname);

#endif

/* end of exam_utils.h */
